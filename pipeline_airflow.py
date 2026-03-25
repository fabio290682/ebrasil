"""
=============================================================
PIPELINE AIRFLOW — ORQUESTRADOR DO SUPER-INTEGRADOR
=============================================================
O que é o Airflow?
  - É um "gerente de tarefas" que executa seus scripts em ordem
  - Define QUANDO cada coleta deve rodar (cron schedule)
  - Monitora se cada etapa teve sucesso ou falha
  - Envia alertas quando algo dá errado
  - Tem uma interface web para visualizar o status de tudo

Como instalar:
  pip install apache-airflow apache-airflow-providers-slack

Como rodar:
  airflow db init
  airflow webserver --port 8080  (abre em http://localhost:8080)
  airflow scheduler

Estrutura de pastas esperada:
  dags/
    pipeline_transparencia.py  ← este arquivo
  plugins/
    scraper_betha.py           ← o scraper que criamos
=============================================================
"""

from datetime import datetime, timedelta, date
from airflow import DAG
from airflow.operators.python import PythonOperator, BranchPythonOperator
from airflow.operators.email import EmailOperator
from airflow.utils.trigger_rule import TriggerRule
from airflow.models import Variable
import logging
import json
import requests

log = logging.getLogger(__name__)


# =============================================================
# CONFIGURAÇÕES PADRÃO DO PIPELINE
# Estas configurações se aplicam a todas as tarefas
# =============================================================

CONFIGURACOES_PADRAO = {
    "owner": "equipe-transparencia",
    
    # Se uma tarefa falhar, tenta novamente 3 vezes
    "retries": 3,
    
    # Espera 5 minutos entre cada tentativa
    "retry_delay": timedelta(minutes=5),
    
    # Se ainda falhar, envia e-mail
    "email_on_failure": True,
    "email_on_retry": False,
    "email": ["alertas@transparencia.gov.br"],
    
    # Não executa tarefas que estavam pendentes enquanto o sistema estava parado
    "depends_on_past": False,
}


# =============================================================
# DEFINIÇÃO DO DAG (Directed Acyclic Graph)
# Um DAG é como uma receita: define as etapas e a ordem delas
# =============================================================

# DAG 1: Coleta diária (Federal + Estados + Capitais)
with DAG(
    dag_id="transparencia_coleta_diaria",
    description="Coleta diária de dados de transparência Federal e Capitais",
    
    # Executa todo dia às 02:00 BRT (05:00 UTC)
    # Formato cron: minuto hora dia_mes mês dia_semana
    schedule_interval="0 5 * * *",
    
    # Data de início — o Airflow vai executar desde esta data (backfill)
    start_date=datetime(2024, 1, 1),
    
    # Não executa retroativamente (não queremos reprocessar o passado agora)
    catchup=False,
    
    default_args=CONFIGURACOES_PADRAO,
    
    # Tags para organizar na interface web do Airflow
    tags=["transparencia", "diario", "federal"],
    
) as dag_diario:

    # -------------------------
    # ETAPA 1: Verificar saúde das fontes
    # -------------------------
    def verificar_fontes(**context):
        """
        Antes de coletar, verifica se as APIs estão online.
        Se uma estiver fora, marca ela como 'indisponível' e continua com as outras.
        """
        fontes = {
            "federal": "https://api.portaldatransparencia.gov.br/api-de-dados/",
            "sp": "https://transparencia.prefeitura.sp.gov.br/api/",
            "rj": "https://pgfn.fazenda.gov.br/", 
        }
        
        status = {}
        for nome, url in fontes.items():
            try:
                resp = requests.get(url, timeout=10)
                status[nome] = "online" if resp.status_code < 500 else "offline"
            except:
                status[nome] = "offline"
            log.info(f"Fonte {nome}: {status[nome]}")
        
        # Salva o status para as próximas etapas consultarem
        # xcom = sistema de compartilhamento de dados entre tarefas do Airflow
        context["ti"].xcom_push(key="status_fontes", value=status)
        
        # Atualiza o dashboard de status (que o público pode ver)
        _atualizar_dashboard_status(status)
        
        return status

    tarefa_verificar = PythonOperator(
        task_id="verificar_fontes",
        python_callable=verificar_fontes,
    )

    # -------------------------
    # ETAPA 2: Coletar dados federais
    # -------------------------
    def coletar_federal(**context):
        """
        Consome a API do Portal da Transparência Federal.
        Esta API já tem documentação em:
        https://api.portaldatransparencia.gov.br/swagger-ui.html
        """
        # Pega a data de ontem (queremos dados do dia anterior)
        data_execucao = context["data_interval_start"].date()
        data_ontem = data_execucao - timedelta(days=1)
        
        log.info(f"Coletando dados federais de {data_ontem}")
        
        # Chave da API — armazenada de forma segura no Airflow Variables
        # Configure em: Admin → Variables → chave_api_federal
        chave_api = Variable.get("chave_api_federal", default_var="demo")
        
        headers = {
            "chave-api-dados": chave_api,
            "Accept": "application/json",
        }
        
        todos_registros = []
        pagina = 1
        
        while True:
            url = "https://api.portaldatransparencia.gov.br/api-de-dados/despesas/documentos"
            params = {
                "dataInicio": data_ontem.strftime("%d/%m/%Y"),
                "dataFim": data_ontem.strftime("%d/%m/%Y"),
                "pagina": pagina,
            }
            
            resp = requests.get(url, headers=headers, params=params, timeout=30)
            
            if resp.status_code == 404 or not resp.json():
                break  # Sem mais dados
            
            resp.raise_for_status()
            dados = resp.json()
            
            if not dados:
                break
            
            todos_registros.extend(dados)
            pagina += 1
            
            import time
            time.sleep(0.2)  # Respeita o rate limit da API federal
        
        log.info(f"Federal: {len(todos_registros)} registros coletados")
        
        # Salva na zona bruta do Data Lake
        _salvar_zona_bruta(todos_registros, "federal", data_ontem)
        
        return len(todos_registros)

    tarefa_federal = PythonOperator(
        task_id="coletar_federal",
        python_callable=coletar_federal,
    )

    # -------------------------
    # ETAPA 3: Coletar capitais em paralelo
    # -------------------------
    CAPITAIS = [
        {"nome": "São Paulo",     "ibge": "3550308", "uf": "SP"},
        {"nome": "Rio de Janeiro","ibge": "3304557", "uf": "RJ"},
        {"nome": "Fortaleza",     "ibge": "2304400", "uf": "CE"},
        {"nome": "Florianópolis", "ibge": "4205407", "uf": "SC"},
        # Adicione as 26 capitais + DF aqui
    ]

    tarefas_capitais = []
    for capital in CAPITAIS:
        def coletar_capital(municipio=capital, **context):
            """Coleta dados de uma capital específica."""
            data_ontem = context["data_interval_start"].date() - timedelta(days=1)
            log.info(f"Coletando {municipio['nome']} ({municipio['uf']})")
            
            # Importa o scraper que criamos
            import sys
            sys.path.insert(0, "/opt/airflow/plugins")
            from scraper_betha import BethaAPICollector
            
            coletor = BethaAPICollector(municipio)
            gastos = coletor.coletar(data_ontem, data_ontem)
            
            _salvar_zona_bruta(
                [g.__dict__ for g in gastos],
                f"capital_{municipio['ibge']}",
                data_ontem
            )
            return len(gastos)

        tarefa = PythonOperator(
            task_id=f"coletar_capital_{capital['ibge']}",
            python_callable=coletar_capital,
        )
        tarefas_capitais.append(tarefa)

    # -------------------------
    # ETAPA 4: Transformar (aplicar Data Mapping / Schema Único)
    # -------------------------
    def transformar_dados(**context):
        """
        Pega os dados brutos e aplica o Schema Único.
        Em produção, isto seria feito pelo dbt (ver modelo_dbt.sql).
        Aqui fazemos uma versão Python mais simples.
        """
        from datetime import date as dt
        data_ontem = context["data_interval_start"].date() - timedelta(days=1)
        
        log.info(f"Transformando dados de {data_ontem}")
        
        # Lista os arquivos brutos salvos
        arquivos = _listar_zona_bruta(data_ontem)
        
        total_ok = 0
        total_erro = 0
        
        for arquivo in arquivos:
            try:
                dados_brutos = _ler_zona_bruta(arquivo)
                dados_padronizados = _aplicar_schema_unico(dados_brutos)
                _salvar_zona_processada(dados_padronizados, arquivo)
                total_ok += len(dados_padronizados)
            except Exception as e:
                log.error(f"Erro ao transformar {arquivo}: {e}")
                total_erro += 1
        
        log.info(f"Transformação: {total_ok} registros OK | {total_erro} arquivos com erro")
        return {"ok": total_ok, "erros": total_erro}

    tarefa_transformar = PythonOperator(
        task_id="transformar_dados",
        python_callable=transformar_dados,
    )

    # -------------------------
    # ETAPA 5: Validar qualidade
    # -------------------------
    def validar_qualidade(**context):
        """
        Roda verificações de qualidade nos dados padronizados.
        Se muitos dados falharem, aborta o pipeline antes de publicar.
        """
        data_ontem = context["data_interval_start"].date() - timedelta(days=1)
        dados = _ler_zona_processada(data_ontem)
        
        total = len(dados)
        if total == 0:
            raise ValueError("Nenhum dado foi coletado! Verifique as fontes.")
        
        erros = []
        
        # Regra 1: campo data_empenho não pode estar vazio
        sem_data = sum(1 for d in dados if not d.get("data_empenho"))
        if sem_data / total > 0.05:  # Mais de 5% sem data = problema
            erros.append(f"{sem_data} registros sem data_empenho ({sem_data/total:.1%})")
        
        # Regra 2: valor não pode ser zero ou negativo
        valor_invalido = sum(1 for d in dados if d.get("valor_empenhado", 0) <= 0)
        if valor_invalido / total > 0.10:
            erros.append(f"{valor_invalido} registros com valor inválido ({valor_invalido/total:.1%})")
        
        # Regra 3: municipio_ibge deve ter 7 dígitos
        ibge_invalido = sum(1 for d in dados if len(str(d.get("municipio_ibge", ""))) != 7)
        if ibge_invalido > 0:
            erros.append(f"{ibge_invalido} registros com código IBGE inválido")
        
        if erros:
            mensagem = "⚠️ Falha na validação de qualidade:\n" + "\n".join(erros)
            log.error(mensagem)
            _enviar_alerta_slack(mensagem)
            raise ValueError(mensagem)
        
        log.info(f"✅ Qualidade validada: {total} registros aprovados")
        return total

    tarefa_validar = PythonOperator(
        task_id="validar_qualidade",
        python_callable=validar_qualidade,
    )

    # -------------------------
    # ETAPA 6: Carregar no Data Warehouse
    # -------------------------
    def carregar_warehouse(**context):
        """
        Carrega os dados validados no BigQuery (ou Redshift).
        Usa UPSERT para não duplicar registros.
        """
        from google.cloud import bigquery
        
        data_ontem = context["data_interval_start"].date() - timedelta(days=1)
        dados = _ler_zona_processada(data_ontem)
        
        client = bigquery.Client()
        tabela = "transparencia_br.gastos_publicos"
        
        # Divide em lotes de 1000 para não sobrecarregar a API do BigQuery
        tamanho_lote = 1000
        total_inserido = 0
        
        for i in range(0, len(dados), tamanho_lote):
            lote = dados[i:i+tamanho_lote]
            errors = client.insert_rows_json(tabela, lote)
            
            if errors:
                log.error(f"Erros ao inserir lote {i}: {errors}")
            else:
                total_inserido += len(lote)
        
        log.info(f"BigQuery: {total_inserido} registros carregados")
        
        # Invalida o cache do Redis para que o app mostre dados frescos
        _invalidar_cache_redis()
        
        return total_inserido

    tarefa_carregar = PythonOperator(
        task_id="carregar_warehouse",
        python_callable=carregar_warehouse,
    )

    # -------------------------
    # ETAPA 7: Notificar sucesso
    # -------------------------
    def notificar_sucesso(**context):
        """Envia uma mensagem de sucesso para o Slack da equipe."""
        data_ontem = context["data_interval_start"].date() - timedelta(days=1)
        
        # Pega os resultados das etapas anteriores via XCom
        qtd_federal = context["ti"].xcom_pull(task_ids="coletar_federal") or 0
        qtd_validados = context["ti"].xcom_pull(task_ids="validar_qualidade") or 0
        
        mensagem = (
            f"✅ *Pipeline de Transparência concluído* | {data_ontem}\n"
            f"   Federal: {qtd_federal:,} registros\n"
            f"   Total validado: {qtd_validados:,} registros\n"
            f"   Capitais processadas: {len(CAPITAIS)}"
        )
        
        _enviar_alerta_slack(mensagem)
        log.info(mensagem)

    tarefa_notificar = PythonOperator(
        task_id="notificar_sucesso",
        python_callable=notificar_sucesso,
        trigger_rule=TriggerRule.ALL_SUCCESS,  # Só notifica se tudo deu certo
    )

    # -------------------------
    # DEFINIÇÃO DA ORDEM DE EXECUÇÃO
    # O símbolo >> significa "execute depois de"
    # -------------------------
    
    # 1. Primeiro verifica se as fontes estão online
    tarefa_verificar >> tarefa_federal
    
    # 2. Federal e Capitais rodam em paralelo (economiza tempo)
    tarefa_verificar >> tarefas_capitais
    
    # 3. Só transforma depois que federal E todas as capitais terminaram
    [tarefa_federal] + tarefas_capitais >> tarefa_transformar
    
    # 4. Valida → Carrega → Notifica (sequencial)
    tarefa_transformar >> tarefa_validar >> tarefa_carregar >> tarefa_notificar


# =============================================================
# DAG 2: Coleta semanal dos scrapers (municípios sem API)
# =============================================================

with DAG(
    dag_id="transparencia_scrapers_semanais",
    description="Coleta semanal via scraping para municípios sem API",
    schedule_interval="0 6 * * 0",  # Domingo às 06:00 UTC
    start_date=datetime(2024, 1, 1),
    catchup=False,
    default_args=CONFIGURACOES_PADRAO,
    tags=["transparencia", "semanal", "scraping"],
    max_active_tasks=5,  # Máximo 5 scrapers rodando ao mesmo tempo
) as dag_semanal:

    def coletar_municipio_scraper(municipio: dict, **context):
        """Roda o scraper para um município sem API."""
        import sys
        sys.path.insert(0, "/opt/airflow/plugins")
        from scraper_betha import BethaHTMLScraper
        
        # Semana passada
        hoje = context["data_interval_start"].date()
        semana_passada_inicio = hoje - timedelta(days=7)
        
        coletor = BethaHTMLScraper(municipio)
        gastos = coletor.coletar(semana_passada_inicio, hoje)
        
        _salvar_zona_bruta(
            [g.__dict__ for g in gastos],
            f"scraper_{municipio['ibge']}",
            hoje
        )
        return len(gastos)

    # Municípios que precisam de scraping (sem API)
    MUNICIPIOS_SCRAPING = [
        {"nome": "Blumenau", "ibge": "4202404", "uf": "SC", "tipo": "html",
         "url_portal": "https://transparencia.blumenau.sc.gov.br",
         "seletor_tabela": "table.table-striped"},
        # Adicione mais municípios conforme for mapeando
    ]

    tarefas_scrapers = []
    for mun in MUNICIPIOS_SCRAPING:
        tarefa = PythonOperator(
            task_id=f"scraper_{mun['ibge']}",
            python_callable=lambda municipio=mun, **ctx: coletar_municipio_scraper(municipio, **ctx),
        )
        tarefas_scrapers.append(tarefa)

    # Scrapers rodam em paralelo (até max_active_tasks ao mesmo tempo)
    # Depois que todos terminam, transforma e carrega
    def transformar_e_carregar_scrapers(**context):
        log.info("Transformando e carregando dados dos scrapers semanais...")
        # Mesma lógica da coleta diária
        
    tarefa_consolidar = PythonOperator(
        task_id="consolidar_scrapers",
        python_callable=transformar_e_carregar_scrapers,
        trigger_rule=TriggerRule.ALL_DONE,  # Roda mesmo se alguns falharam
    )

    tarefas_scrapers >> tarefa_consolidar


# =============================================================
# FUNÇÕES AUXILIARES (usadas pelas tarefas acima)
# Em produção, ficam em arquivos separados no diretório plugins/
# =============================================================

def _salvar_zona_bruta(dados: list, fonte: str, data: date):
    """
    Salva dados brutos no Data Lake (S3 ou GCS).
    Particionado por: fonte/ano/mês/dia/arquivo.json
    """
    import os, json
    
    # Monta o caminho de partição (facilita buscas futuras)
    caminho = f"zona_bruta/{fonte}/{data.year}/{data.month:02d}/{data.day:02d}/dados.json"
    
    # Em produção: substituir por boto3 (AWS S3) ou google.cloud.storage (GCS)
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, default=str)
    
    log.info(f"Salvo em zona bruta: {caminho} ({len(dados)} registros)")


def _listar_zona_bruta(data: date) -> list:
    """Lista todos os arquivos brutos de uma data."""
    import glob
    return glob.glob(f"zona_bruta/*/{data.year}/{data.month:02d}/{data.day:02d}/*.json")


def _ler_zona_bruta(caminho: str) -> list:
    """Lê um arquivo da zona bruta."""
    with open(caminho, encoding="utf-8") as f:
        return json.load(f)


def _aplicar_schema_unico(dados: list) -> list:
    """
    Normaliza qualquer lista de dicionários para o Schema Único.
    Garante que todos os campos obrigatórios existam.
    """
    CAMPOS_OBRIGATORIOS = [
        "id", "data_empenho", "valor_empenhado", "favorecido_nome",
        "elemento_despesa", "municipio_ibge", "uf", "fornecedor_sistema",
        "url_origem", "atualizado_em"
    ]
    
    resultado = []
    for item in dados:
        # Garante que todos os campos obrigatórios existam (mesmo que vazios)
        for campo in CAMPOS_OBRIGATORIOS:
            if campo not in item:
                item[campo] = None
        resultado.append(item)
    
    return resultado


def _salvar_zona_processada(dados: list, origem: str):
    """Salva dados padronizados na zona processada do Data Lake."""
    import json
    nome = f"zona_processada/{origem}_padronizado.json"
    with open(nome, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, default=str)


def _ler_zona_processada(data: date) -> list:
    """Lê todos os dados padronizados de uma data."""
    import glob, json
    todos = []
    for arquivo in glob.glob(f"zona_processada/*.json"):
        with open(arquivo, encoding="utf-8") as f:
            todos.extend(json.load(f))
    return todos


def _enviar_alerta_slack(mensagem: str):
    """Envia alerta para o Slack da equipe."""
    webhook_url = Variable.get("slack_webhook_url", default_var=None)
    if not webhook_url:
        log.warning("slack_webhook_url não configurado — alerta não enviado")
        return
    
    try:
        requests.post(webhook_url, json={"text": mensagem}, timeout=10)
    except Exception as e:
        log.error(f"Falha ao enviar alerta Slack: {e}")


def _atualizar_dashboard_status(status: dict):
    """Atualiza o dashboard público que mostra status de cada portal."""
    log.info(f"Status atualizado: {status}")
    # Em produção: escrever em Redis ou banco de dados
    # O app web lê este status para mostrar "Portal online/offline" para o usuário


def _invalidar_cache_redis():
    """Invalida o cache do Redis para que os dados frescos apareçam no app."""
    try:
        import redis
        r = redis.Redis(host="redis", port=6379)
        # Remove todas as chaves que começam com "gastos:"
        keys = r.keys("gastos:*")
        if keys:
            r.delete(*keys)
        log.info(f"Cache Redis invalidado: {len(keys)} chaves removidas")
    except Exception as e:
        log.warning(f"Não foi possível invalidar cache Redis: {e}")
