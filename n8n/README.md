# Arquitetura Dinamica n8n - Integracao Nacional

Este pacote implementa o fluxo mestre orientado por catalogo de fontes (sem fluxo por cidade).

## Arquivos

- `sql/schema_postgres.sql`: tabelas de fontes e dados unificados.
- `sql/migration_002_agentes_publicos.sql`: migracao para campos de agentes politicos.
- `sql/migration_003_ia_enriquecimento.sql`: migracao para campos de classificacao por IA.
- `code/normalizador_universal.js`: tradutor para Schema Unico.
- `code/normalizador_camara_ceap.js`: normalizador especifico da Camara.
- `code/normalizador_senado_ceaps.js`: normalizador especifico do Senado.
- `code/normalizador_ministerios.js`: normalizador especifico do Executivo Federal.
- `workflows/integracao_nacional_dinamica.json`: workflow principal com loop e batch.
- `workflows/integracao_politicos_federal.json`: workflow dedicado a Deputados, Senadores e Ministerios (normalizadores ja embutidos).
- `workflows/integracao_nacional_ia.json`: workflow com etapa de IA para classificar risco/categoria de cada gasto.
- `workflows/alerta_falhas_fontes.json`: workflow de alerta via Error Trigger.

## Passo a passo

1. Criar tabelas no PostgreSQL/Supabase executando:

```sql
\i n8n/sql/schema_postgres.sql
\i n8n/sql/migration_002_agentes_publicos.sql
\i n8n/sql/migration_003_ia_enriquecimento.sql
```

2. Importar workflows no n8n (menu `Import from file`):
- `integracao_nacional_dinamica.json`
- `integracao_politicos_federal.json`
- `integracao_nacional_ia.json` (opcional, recomendado)
- `alerta_falhas_fontes.json`

3. Configurar credenciais:
- Substituir `REPLACE_POSTGRES_CREDENTIAL_ID` por sua credencial Postgres.
- Substituir webhook do Slack em `alerta_falhas_fontes.json`.
- Definir `OPENAI_API_KEY` no ambiente do n8n para usar o fluxo com IA.

4. Cadastrar fontes no catalogo:

```sql
INSERT INTO fontes_transparencia
(ativo, nome_fonte, esfera, uf, municipio_nome, municipio_ibge, sistema_fornecedor, tipo_coleta, metodo_http, url_base, path_endpoint)
VALUES
(true, 'Portal Federal', 'federal', 'DF', 'Brasilia', '5300108', 'govbr', 'api_json', 'GET', 'https://api.portaldatransparencia.gov.br', '/despesas');
```

5. Ativar os workflows desejados.

## O que a IA faz no fluxo

No workflow `integracao_nacional_ia.json`, cada registro passa por classificacao de IA e recebe:
- `categoria_ia`
- `risco_ia` (`baixo`, `medio`, `alto`)
- `justificativa_ia`

Esses campos sao persistidos na tabela `gastos_publicos_unificados`.

## Observacoes importantes

- O normalizador usa fallback de campos e `mapeamento_campos` por fonte para lidar com JSON heterogeneo.
- O design permite incluir novas cidades apenas inserindo uma linha em `fontes_transparencia`.
- Para fontes HTML, mantenha `tipo_coleta='html_scraping'` e trate em um branch dedicado (Playwright worker externo) sem quebrar o fluxo nacional.
