"""
=============================================================
SCRAPER PARA PORTAIS DE TRANSPARÊNCIA - SISTEMA BETHA
=============================================================
O que este arquivo faz:
  - Acessa portais de prefeituras que usam o sistema Betha
  - Preenche os filtros de data automaticamente
  - Lê a tabela de resultados (empenhos/gastos)
  - Salva os dados no formato do nosso Schema Único

Como o Betha funciona:
  - A maioria das prefeituras que usa Betha tem URLs no padrão:
    https://transparencia.MUNICIPIO.sc.gov.br/api/despesas/empenhos
  - Algumas têm API REST (mais fácil), outras só têm página HTML (scraping)

Pré-requisitos (instale com pip):
  pip install requests playwright pandas python-dotenv
  playwright install chromium
=============================================================
"""

import requests
import pandas as pd
import json
import logging
import time
import uuid
from datetime import datetime, date
from dataclasses import dataclass, asdict
from typing import Optional
from playwright.sync_api import sync_playwright  # Para portais que só têm HTML

# Configuração do log — registra tudo que acontece para debug
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("scraper_betha.log"),  # Salva em arquivo
        logging.StreamHandler()                    # Mostra no terminal
    ]
)
log = logging.getLogger(__name__)


# =============================================================
# SCHEMA ÚNICO — A estrutura que todo dado deve seguir
# Independente de como o Betha chama o campo, o resultado
# sempre vai ter esses mesmos nomes.
# =============================================================

@dataclass
class GastoPublico:
    """
    Esta classe é o nosso 'molde' para um gasto público.
    Todo dado coletado — de qualquer município — vai ser
    transformado para caber neste molde.
    """
    id: str                          # ID único gerado por nós (UUID)
    data_empenho: str                # Data no formato YYYY-MM-DD
    valor_empenhado: float           # Valor em reais (decimal)
    favorecido_nome: str             # Nome do fornecedor/beneficiário
    favorecido_cnpj_cpf: str         # CNPJ ou CPF (opcional)
    elemento_despesa: str            # Código do elemento (ex: 339039)
    fonte_recurso: Optional[str]     # Origem do dinheiro (opcional)
    funcao_governo: Optional[str]    # Área de governo (ex: Educação)
    numero_empenho: Optional[str]    # Número do documento
    municipio_ibge: str              # Código IBGE do município (7 dígitos)
    uf: str                          # Estado (ex: SC, CE, SP)
    fornecedor_sistema: str          # Sistema usado (Betha, Fiorilli, etc.)
    url_origem: str                  # URL de onde o dado veio
    atualizado_em: str               # Quando coletamos este dado


# =============================================================
# CONFIGURAÇÃO DOS MUNICÍPIOS
# Cada município tem sua URL e às vezes pequenas variações.
# Começamos com um dicionário simples — depois isso vai para
# um banco de dados.
# =============================================================

MUNICIPIOS_BETHA = [
    {
        "nome": "Florianópolis",
        "ibge": "4205407",
        "uf": "SC",
        "tipo": "api",  # Este município tem API REST
        "url_api": "https://transparencia.pmf.sc.gov.br/api/despesas/empenhos",
        "url_portal": "https://transparencia.pmf.sc.gov.br",
    },
    {
        "nome": "Joinville",
        "ibge": "4209102",
        "uf": "SC",
        "tipo": "api",
        "url_api": "https://transparencia.joinville.sc.gov.br/api/despesas/empenhos",
        "url_portal": "https://transparencia.joinville.sc.gov.br",
    },
    {
        "nome": "Blumenau",
        "ibge": "4202404",
        "uf": "SC",
        "tipo": "html",  # Este só tem página HTML (sem API)
        "url_portal": "https://transparencia.blumenau.sc.gov.br",
        "seletor_tabela": "table.table-empenhos",  # Classe CSS da tabela no HTML
    },
    # Adicione mais municípios aqui conforme for mapeando
]


# =============================================================
# CLASSE PRINCIPAL: BethaAPICollector
# Responsável por coletar dados de municípios COM API REST
# =============================================================

class BethaAPICollector:
    """
    Coleta dados de portais Betha que disponibilizam API REST.
    A API do Betha geralmente retorna JSON — muito mais fácil de processar.
    """

    def __init__(self, municipio: dict):
        self.municipio = municipio
        self.session = requests.Session()
        # Nos identificamos como um navegador normal para evitar bloqueios
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (compatible; TransparenciaBR/1.0)",
            "Accept": "application/json",
        })

    def coletar(self, data_inicio: date, data_fim: date) -> list[GastoPublico]:
        """
        Coleta empenhos de um período específico.
        
        Parâmetros:
          data_inicio: Data de início (ex: date(2024, 1, 1))
          data_fim:    Data de fim   (ex: date(2024, 1, 31))
        
        Retorna:
          Lista de GastoPublico já no Schema Único
        """
        log.info(f"[{self.municipio['nome']}] Iniciando coleta via API: {data_inicio} → {data_fim}")
        
        gastos = []
        pagina = 1
        
        while True:
            # A API do Betha usa paginação — precisamos ir página por página
            try:
                resposta = self._buscar_pagina(data_inicio, data_fim, pagina)
            except Exception as e:
                log.error(f"[{self.municipio['nome']}] Erro na página {pagina}: {e}")
                break
            
            if not resposta or not resposta.get("content"):
                log.info(f"[{self.municipio['nome']}] Sem mais dados na página {pagina}. Finalizando.")
                break
            
            for item_bruto in resposta["content"]:
                gasto = self._mapear_para_schema(item_bruto)
                if gasto:
                    gastos.append(gasto)
            
            # Verifica se há próxima página
            if resposta.get("last", True):
                break
            
            pagina += 1
            time.sleep(0.5)  # Pausa para não sobrecarregar o servidor
        
        log.info(f"[{self.municipio['nome']}] Total coletado: {len(gastos)} registros")
        return gastos

    def _buscar_pagina(self, data_inicio: date, data_fim: date, pagina: int) -> dict:
        """Faz a requisição HTTP para uma página específica da API."""
        params = {
            "dataInicio": data_inicio.strftime("%Y-%m-%d"),
            "dataFim": data_fim.strftime("%Y-%m-%d"),
            "page": pagina - 1,   # Betha usa página 0-indexed
            "size": 100,          # 100 registros por página
            "sort": "dataEmpenho,asc",
        }
        
        url = self.municipio["url_api"]
        resposta = self.session.get(url, params=params, timeout=30)
        
        # Se o servidor retornar erro, levantamos uma exceção
        resposta.raise_for_status()
        
        return resposta.json()

    def _mapear_para_schema(self, item: dict) -> Optional[GastoPublico]:
        """
        Converte um item no formato BETHA para o nosso Schema Único.
        
        Este é o coração do Data Mapping:
        - O Betha chama de "dataEmpenho", nós chamamos de "data_empenho"
        - O Betha chama de "fornecedor.nomeRazaoSocial", nós de "favorecido_nome"
        - E assim por diante...
        """
        try:
            return GastoPublico(
                id=str(uuid.uuid4()),
                
                # Datas: o Betha envia como "2024-06-15T00:00:00" — pegamos só a data
                data_empenho=item.get("dataEmpenho", "")[:10],
                
                # Valor: o Betha pode enviar como string "12.500,00" — convertemos para float
                valor_empenhado=self._converter_valor(item.get("valorEmpenho", 0)),
                
                # Fornecedor: o Betha coloca dentro de um sub-objeto "fornecedor"
                favorecido_nome=item.get("fornecedor", {}).get("nomeRazaoSocial", "NÃO INFORMADO"),
                favorecido_cnpj_cpf=self._limpar_cnpj(
                    item.get("fornecedor", {}).get("cpfCnpj", "")
                ),
                
                # Elemento de despesa: às vezes vem com pontos (33.90.39), removemos
                elemento_despesa=item.get("elementoDespesa", {}).get("codigo", "").replace(".", ""),
                
                # Campos opcionais — nem todo município preenche
                fonte_recurso=item.get("fonteRecurso", {}).get("codigo"),
                funcao_governo=item.get("funcao", {}).get("descricao"),
                numero_empenho=str(item.get("numero", "")),
                
                # Metadados: de onde veio este dado
                municipio_ibge=self.municipio["ibge"],
                uf=self.municipio["uf"],
                fornecedor_sistema="Betha",
                url_origem=self.municipio["url_portal"],
                atualizado_em=datetime.now().isoformat(),
            )
        except Exception as e:
            log.warning(f"Erro ao mapear item: {e} | Item: {item}")
            return None  # Descarta o item com problema, mas não para o processo

    def _converter_valor(self, valor) -> float:
        """Converte diferentes formatos de valor para float."""
        if isinstance(valor, (int, float)):
            return float(valor)
        if isinstance(valor, str):
            # Remove R$, pontos de milhar, troca vírgula por ponto
            valor = valor.replace("R$", "").replace(".", "").replace(",", ".").strip()
            return float(valor) if valor else 0.0
        return 0.0

    def _limpar_cnpj(self, cnpj: str) -> str:
        """Remove formatação do CNPJ/CPF, deixa só números."""
        import re
        return re.sub(r"\D", "", cnpj or "")


# =============================================================
# CLASSE: BethaHTMLScraper
# Para municípios que NÃO têm API — precisamos simular um navegador
# =============================================================

class BethaHTMLScraper:
    """
    Usa Playwright para abrir o portal no navegador (invisível),
    preencher os filtros de data e ler a tabela de resultados.
    
    Playwright é como um robô que controla um Chrome real.
    """

    def __init__(self, municipio: dict):
        self.municipio = municipio

    def coletar(self, data_inicio: date, data_fim: date) -> list[GastoPublico]:
        log.info(f"[{self.municipio['nome']}] Iniciando scraping HTML: {data_inicio} → {data_fim}")
        gastos = []

        with sync_playwright() as p:
            # Abre um Chrome invisível (headless=True = sem janela)
            browser = p.chromium.launch(headless=True)
            pagina = browser.new_page()
            
            try:
                # 1. Acessa o portal
                pagina.goto(self.municipio["url_portal"] + "/despesas/empenhos", timeout=30000)
                pagina.wait_for_load_state("networkidle")
                
                # 2. Preenche o filtro de data início
                pagina.fill('input[name="dataInicio"], input[id*="dataInicio"]',
                            data_inicio.strftime("%d/%m/%Y"))
                
                # 3. Preenche o filtro de data fim
                pagina.fill('input[name="dataFim"], input[id*="dataFim"]',
                            data_fim.strftime("%d/%m/%Y"))
                
                # 4. Clica no botão de buscar
                pagina.click('button[type="submit"], button:has-text("Pesquisar"), button:has-text("Filtrar")')
                pagina.wait_for_load_state("networkidle")
                time.sleep(2)  # Aguarda a tabela carregar
                
                # 5. Lê todas as páginas da tabela
                while True:
                    gastos_pagina = self._ler_tabela(pagina)
                    gastos.extend(gastos_pagina)
                    
                    # Tenta ir para próxima página
                    botao_prox = pagina.query_selector('a:has-text("Próximo"), a[aria-label="Next"]')
                    if not botao_prox or not botao_prox.is_enabled():
                        break
                    
                    botao_prox.click()
                    pagina.wait_for_load_state("networkidle")
                    time.sleep(1)
                    
            except Exception as e:
                log.error(f"[{self.municipio['nome']}] Erro no scraping: {e}")
            finally:
                browser.close()

        log.info(f"[{self.municipio['nome']}] Total coletado: {len(gastos)} registros")
        return gastos

    def _ler_tabela(self, pagina) -> list[GastoPublico]:
        """Lê as linhas da tabela HTML e mapeia para o Schema Único."""
        gastos = []
        
        # Pega todas as linhas da tabela (exceto o cabeçalho)
        linhas = pagina.query_selector_all(
            f'{self.municipio.get("seletor_tabela", "table")} tbody tr'
        )
        
        for linha in linhas:
            celulas = linha.query_selector_all("td")
            if len(celulas) < 4:
                continue  # Linha vazia ou inválida
            
            try:
                # A posição das colunas pode variar — este é um exemplo genérico
                # Em produção, você vai mapear coluna por coluna para cada portal
                gasto = GastoPublico(
                    id=str(uuid.uuid4()),
                    data_empenho=self._normalizar_data(celulas[0].inner_text().strip()),
                    numero_empenho=celulas[1].inner_text().strip(),
                    favorecido_nome=celulas[2].inner_text().strip(),
                    valor_empenhado=self._converter_valor(celulas[3].inner_text().strip()),
                    elemento_despesa=celulas[4].inner_text().strip() if len(celulas) > 4 else "",
                    favorecido_cnpj_cpf="",
                    fonte_recurso=None,
                    funcao_governo=None,
                    municipio_ibge=self.municipio["ibge"],
                    uf=self.municipio["uf"],
                    fornecedor_sistema="Betha",
                    url_origem=self.municipio["url_portal"],
                    atualizado_em=datetime.now().isoformat(),
                )
                gastos.append(gasto)
            except Exception as e:
                log.warning(f"Erro ao ler linha da tabela: {e}")
        
        return gastos

    def _normalizar_data(self, texto: str) -> str:
        """Converte DD/MM/YYYY para YYYY-MM-DD (padrão ISO)."""
        for fmt in ["%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d"]:
            try:
                return datetime.strptime(texto, fmt).strftime("%Y-%m-%d")
            except ValueError:
                continue
        return texto  # Retorna como veio se não conseguir converter

    def _converter_valor(self, texto: str) -> float:
        """Converte 'R$ 12.500,00' para 12500.0"""
        import re
        texto = re.sub(r"[R$\s]", "", texto).replace(".", "").replace(",", ".")
        try:
            return float(texto)
        except ValueError:
            return 0.0


# =============================================================
# FUNÇÃO PRINCIPAL: Orquestra a coleta de todos os municípios
# =============================================================

def coletar_todos(data_inicio: date, data_fim: date, salvar_csv: bool = True):
    """
    Coleta dados de todos os municípios configurados.
    
    Parâmetros:
      data_inicio: Data de início da coleta
      data_fim:    Data de fim da coleta
      salvar_csv:  Se True, salva resultado em CSV
    
    Retorna:
      DataFrame com todos os gastos no Schema Único
    """
    todos_gastos = []
    erros = []

    for municipio in MUNICIPIOS_BETHA:
        try:
            if municipio["tipo"] == "api":
                coletor = BethaAPICollector(municipio)
            else:
                coletor = BethaHTMLScraper(municipio)
            
            gastos = coletor.coletar(data_inicio, data_fim)
            todos_gastos.extend([asdict(g) for g in gastos])
            
        except Exception as e:
            log.error(f"FALHA TOTAL em {municipio['nome']}: {e}")
            erros.append({"municipio": municipio["nome"], "erro": str(e), "ts": datetime.now().isoformat()})

    # Converte para DataFrame (tabela) para facilitar manipulação
    df = pd.DataFrame(todos_gastos)
    
    if salvar_csv and not df.empty:
        nome_arquivo = f"gastos_betha_{data_inicio}_{data_fim}.csv"
        df.to_csv(nome_arquivo, index=False, encoding="utf-8-sig")
        log.info(f"Dados salvos em: {nome_arquivo}")
    
    # Salva log de erros separado
    if erros:
        with open("erros_coleta.json", "w") as f:
            json.dump(erros, f, ensure_ascii=False, indent=2)
        log.warning(f"{len(erros)} municípios falharam. Veja erros_coleta.json")
    
    log.info(f"Coleta finalizada. Total: {len(todos_gastos)} registros | Erros: {len(erros)} municípios")
    return df


# =============================================================
# PONTO DE ENTRADA — execute este arquivo diretamente para testar
# python scraper_betha.py
# =============================================================

if __name__ == "__main__":
    # Teste: coleta o mês de junho de 2024
    df = coletar_todos(
        data_inicio=date(2024, 6, 1),
        data_fim=date(2024, 6, 30),
        salvar_csv=True
    )
    
    print(f"\n✅ Coleta concluída!")
    print(f"   Registros: {len(df)}")
    if not df.empty:
        print(f"   Municípios: {df['municipio_ibge'].nunique()}")
        print(f"   Valor total: R$ {df['valor_empenhado'].sum():,.2f}")
        print(f"\nPrimeiros registros:")
        print(df[["data_empenho", "favorecido_nome", "valor_empenhado", "municipio_ibge"]].head())
