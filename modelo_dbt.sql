-- =============================================================
-- MODELOS dbt — DATA MAPPING E SCHEMA ÚNICO
-- =============================================================
-- O que é o dbt (Data Build Tool)?
--   - É uma ferramenta que organiza as transformações SQL
--   - Cada arquivo .sql é um "modelo" (uma tabela ou view)
--   - O dbt controla a ordem de execução e testa a qualidade
--   - Roda dentro do BigQuery, Redshift, Snowflake, etc.
--
-- Estrutura de pastas dbt:
--   models/
--     staging/          ← Dados brutos padronizados (1 arquivo por fonte)
--       stg_federal.sql
--       stg_betha.sql
--       stg_fiorilli.sql
--       stg_ipm.sql
--     intermediate/     ← Transformações intermediárias
--       int_gastos_normalizados.sql
--     marts/            ← Tabelas finais que o app consome
--       gastos_publicos.sql
--       municipios.sql
--       dim_elemento_despesa.sql
--   tests/              ← Testes de qualidade dos dados
--   macros/             ← Funções SQL reutilizáveis
-- =============================================================


-- =============================================================
-- ARQUIVO: models/staging/stg_federal.sql
-- Padroniza os dados da API Federal para o Schema Único
-- =============================================================

-- {{ config(...) }} é sintaxe do dbt para configurar a tabela
{{ config(
    materialized='incremental',
    unique_key='id',
    partition_by={'field': 'data_empenho', 'data_type': 'date'},
    cluster_by=['uf', 'municipio_ibge']
) }}

/*
  'incremental' significa que o dbt só processa registros NOVOS
  em vez de recriar a tabela inteira toda vez.
  Muito mais eficiente com volumes grandes!
*/

SELECT
    -- Gera um ID único combinando a fonte com o número do documento
    {{ dbt_utils.generate_surrogate_key(['numero_empenho', '"federal"']) }} AS id,
    
    -- Data: a API federal envia como DD/MM/YYYY — convertemos para DATE
    PARSE_DATE('%d/%m/%Y', data_empenho_raw)    AS data_empenho,
    
    -- Valor: garantimos que é NUMERIC com 2 casas decimais
    SAFE_CAST(REPLACE(REPLACE(valor_empenho_raw, '.', ''), ',', '.') AS NUMERIC)
                                                AS valor_empenhado,
    
    -- Favorecido: remove espaços extras e padroniza maiúsculas
    UPPER(TRIM(nome_favorecido))                AS favorecido_nome,
    
    -- CNPJ/CPF: remove formatação (pontos, traços, barras)
    REGEXP_REPLACE(cpf_cnpj_favorecido, r'[.\-/]', '')
                                                AS favorecido_cnpj_cpf,
    
    -- Elemento de despesa: padroniza para 6 dígitos sem pontos
    LPAD(REGEXP_REPLACE(elemento_despesa, r'\.', ''), 6, '0')
                                                AS elemento_despesa,
    
    -- Fonte de recurso
    TRIM(fonte_recurso)                         AS fonte_recurso,
    
    -- Função de governo: usa a descrição textual
    TRIM(nome_funcao)                           AS funcao_governo,
    
    -- Número do empenho
    CAST(numero_empenho AS STRING)              AS numero_empenho,
    
    -- Código IBGE do município (7 dígitos)
    -- A API federal usa código de 6 dígitos — completamos com 0 à direita
    LPAD(CAST(codigo_ibge AS STRING), 7, '0')  AS municipio_ibge,
    
    -- UF extraída da tabela de municípios
    uf,
    
    -- Metadados de rastreabilidade
    'PortalFederal'                             AS fornecedor_sistema,
    'https://api.portaldatransparencia.gov.br'  AS url_origem,
    CURRENT_TIMESTAMP()                         AS atualizado_em

FROM {{ source('raw', 'empenhos_federal_raw') }}

-- No modo incremental, só pega registros mais recentes que o último processado
{% if is_incremental() %}
WHERE data_empenho_raw >= (
    SELECT MAX(data_empenho) FROM {{ this }}
)
{% endif %}


-- =============================================================
-- ARQUIVO: models/staging/stg_betha.sql
-- Padroniza dados de municípios que usam o sistema Betha
-- =============================================================

{{ config(
    materialized='incremental',
    unique_key='id',
    partition_by={'field': 'data_empenho', 'data_type': 'date'},
) }}

SELECT
    {{ dbt_utils.generate_surrogate_key(['municipio_ibge', 'numero_empenho', '"betha"']) }}
                                                AS id,
    
    -- O Betha envia data no formato ISO: YYYY-MM-DDTHH:MM:SS
    -- Pegamos só a parte da data
    DATE(TIMESTAMP(data_empenho_betha))         AS data_empenho,
    
    -- No Betha, o valor já vem como número (mais fácil)
    SAFE_CAST(valor_empenho AS NUMERIC)         AS valor_empenhado,
    
    UPPER(TRIM(nome_razao_social))              AS favorecido_nome,
    REGEXP_REPLACE(cpf_cnpj, r'[.\-/]', '')    AS favorecido_cnpj_cpf,
    
    -- Elemento: o Betha usa formato "3.3.90.39" — removemos os pontos
    REGEXP_REPLACE(cod_elemento_despesa, r'\.', '')
                                                AS elemento_despesa,
    
    TRIM(cod_fonte_recurso)                     AS fonte_recurso,
    TRIM(dsc_funcao)                            AS funcao_governo,
    CAST(nr_empenho AS STRING)                  AS numero_empenho,
    
    -- municipio_ibge já vem correto do nosso scraper
    municipio_ibge,
    uf,
    
    'Betha'                                     AS fornecedor_sistema,
    url_portal                                  AS url_origem,
    CURRENT_TIMESTAMP()                         AS atualizado_em

FROM {{ source('raw', 'empenhos_betha_raw') }}

{% if is_incremental() %}
WHERE data_empenho_betha >= (
    SELECT MAX(data_empenho) FROM {{ this }}
)
{% endif %}


-- =============================================================
-- ARQUIVO: models/staging/stg_fiorilli.sql  
-- Padroniza dados do sistema Fiorilli
-- =============================================================

{{ config(materialized='incremental', unique_key='id') }}

SELECT
    {{ dbt_utils.generate_surrogate_key(['cod_municipio_ibge', 'num_empenho', '"fiorilli"']) }}
                                                AS id,
    
    -- Fiorilli envia datas como DD/MM/YYYY
    PARSE_DATE('%d/%m/%Y', dt_empenho)          AS data_empenho,
    
    -- Fiorilli usa vírgula como separador decimal
    SAFE_CAST(
        REPLACE(REPLACE(vl_empenho, '.', ''), ',', '.') AS NUMERIC
    )                                           AS valor_empenhado,
    
    UPPER(TRIM(nm_credor))                      AS favorecido_nome,
    REGEXP_REPLACE(nr_cpf_cnpj, r'[.\-/]', '') AS favorecido_cnpj_cpf,
    
    -- Fiorilli usa formato 339039 (já sem pontos — mais fácil)
    LPAD(CAST(cd_elemento AS STRING), 6, '0')  AS elemento_despesa,
    
    CAST(cd_fonte AS STRING)                    AS fonte_recurso,
    nm_funcao                                   AS funcao_governo,
    CAST(num_empenho AS STRING)                 AS numero_empenho,
    LPAD(CAST(cod_municipio_ibge AS STRING), 7, '0')
                                                AS municipio_ibge,
    sg_uf                                       AS uf,
    
    'Fiorilli'                                  AS fornecedor_sistema,
    url_origem,
    CURRENT_TIMESTAMP()                         AS atualizado_em

FROM {{ source('raw', 'empenhos_fiorilli_raw') }}

{% if is_incremental() %}
WHERE dt_empenho >= (
    SELECT FORMAT_DATE('%d/%m/%Y', MAX(data_empenho)) FROM {{ this }}
)
{% endif %}


-- =============================================================
-- ARQUIVO: models/marts/gastos_publicos.sql
-- TABELA FINAL — União de todas as fontes padronizadas
-- Esta é a tabela que o app vai consultar
-- =============================================================

{{ config(
    materialized='table',
    partition_by={'field': 'data_empenho', 'data_type': 'date', 'granularity': 'month'},
    cluster_by=['uf', 'municipio_ibge', 'elemento_despesa'],
    labels={'equipe': 'transparencia', 'ambiente': 'producao'}
) }}

/*
  UNION ALL: combina as tabelas de staging em uma só.
  O Schema Único garante que todas têm as mesmas colunas,
  então o UNION funciona perfeitamente.
*/

WITH todas_fontes AS (
    -- Federal
    SELECT * FROM {{ ref('stg_federal') }}
    
    UNION ALL
    
    -- Sistema Betha (SC, PR, RS principalmente)
    SELECT * FROM {{ ref('stg_betha') }}
    
    UNION ALL
    
    -- Sistema Fiorilli (SP, MG principalmente)
    SELECT * FROM {{ ref('stg_fiorilli') }}

    -- Adicione mais fontes aqui conforme for integrando:
    -- UNION ALL SELECT * FROM {{ ref('stg_ipm') }}
    -- UNION ALL SELECT * FROM {{ ref('stg_govbr') }}
),

-- Remove duplicatas que podem existir entre fontes
-- (ex: um estado que aparece tanto na API federal quanto na API estadual)
sem_duplicatas AS (
    SELECT *
    FROM todas_fontes
    QUALIFY ROW_NUMBER() OVER (
        PARTITION BY municipio_ibge, numero_empenho, elemento_despesa
        ORDER BY atualizado_em DESC  -- Fica com o registro mais recente
    ) = 1
),

-- Enriquece com informações do município (nome, região, população)
enriquecido AS (
    SELECT
        g.*,
        m.nome_municipio,
        m.nome_regiao,
        m.populacao_estimada,
        m.porte_municipio,  -- Pequeno, Médio, Grande, Metrópole
        
        -- Calcula gasto per capita (útil para comparações)
        SAFE_DIVIDE(g.valor_empenhado, m.populacao_estimada) AS gasto_per_capita,
        
        -- Extrai ano e mês para facilitar filtros no app
        EXTRACT(YEAR FROM g.data_empenho)   AS ano,
        EXTRACT(MONTH FROM g.data_empenho)  AS mes,
        
        -- Classifica o porte do empenho
        CASE
            WHEN g.valor_empenhado < 1000        THEN 'Pequeno (< R$ 1 mil)'
            WHEN g.valor_empenhado < 10000       THEN 'Médio (R$ 1-10 mil)'
            WHEN g.valor_empenhado < 100000      THEN 'Grande (R$ 10-100 mil)'
            WHEN g.valor_empenhado < 1000000     THEN 'Muito grande (R$ 100 mil - 1 mi)'
            ELSE                                      'Mega (> R$ 1 milhão)'
        END                                     AS porte_empenho

    FROM sem_duplicatas g
    LEFT JOIN {{ ref('dim_municipios') }} m
        ON g.municipio_ibge = m.codigo_ibge
)

SELECT * FROM enriquecido


-- =============================================================
-- ARQUIVO: models/marts/dim_municipios.sql
-- Tabela de dimensão com dados de todos os municípios brasileiros
-- =============================================================

{{ config(materialized='table') }}

SELECT
    codigo_ibge,
    nome_municipio,
    uf,
    nome_estado,
    nome_regiao,
    SAFE_CAST(populacao_estimada AS INT64) AS populacao_estimada,
    CASE
        WHEN SAFE_CAST(populacao_estimada AS INT64) < 5000        THEN 'Micro (<5mil hab)'
        WHEN SAFE_CAST(populacao_estimada AS INT64) < 20000       THEN 'Pequeno (5-20mil)'
        WHEN SAFE_CAST(populacao_estimada AS INT64) < 100000      THEN 'Médio (20-100mil)'
        WHEN SAFE_CAST(populacao_estimada AS INT64) < 500000      THEN 'Grande (100-500mil)'
        ELSE                                                           'Metrópole (>500mil)'
    END AS porte_municipio,
    latitude,
    longitude

FROM {{ source('raw', 'municipios_ibge') }}


-- =============================================================
-- ARQUIVO: tests/generic/test_schema_unico.yml
-- Testes automáticos de qualidade — o dbt executa antes de publicar
-- =============================================================

/*
  Este não é SQL puro — é YAML (arquivo de configuração).
  Salve como: tests/generic/test_schema_unico.yml

  O dbt converte estes testes em SQL e os executa automaticamente.
  Se algum falhar, o pipeline para e envia alerta.
*/

-- version: 2
-- 
-- models:
--   - name: gastos_publicos
--     description: "Tabela unificada de gastos públicos de todos os municípios"
--     
--     columns:
--       - name: id
--         description: "Identificador único do empenho"
--         tests:
--           - unique          # Não pode haver dois IDs iguais
--           - not_null        # Não pode ser vazio
--       
--       - name: data_empenho
--         tests:
--           - not_null
--           - dbt_utils.expression_is_true:
--               expression: ">= '2000-01-01'"  # Data não pode ser antes de 2000
--       
--       - name: valor_empenhado
--         tests:
--           - not_null
--           - dbt_utils.expression_is_true:
--               expression: "> 0"   # Valor deve ser positivo
--       
--       - name: municipio_ibge
--         tests:
--           - not_null
--           - dbt_utils.expression_is_true:
--               expression: "LENGTH(municipio_ibge) = 7"  # Deve ter 7 dígitos
--       
--       - name: uf
--         tests:
--           - not_null
--           - accepted_values:
--               values: ['AC','AL','AP','AM','BA','CE','DF','ES','GO','MA',
--                        'MT','MS','MG','PA','PB','PR','PE','PI','RJ','RN',
--                        'RS','RO','RR','SC','SP','SE','TO']
--       
--       - name: fornecedor_sistema
--         tests:
--           - accepted_values:
--               values: ['PortalFederal', 'Betha', 'Fiorilli', 'IPM', 'Manual']
-- 
-- 
-- ARQUIVO: dbt_project.yml (configuração principal do dbt)
-- 
-- name: 'transparencia_br'
-- version: '1.0.0'
-- 
-- profile: 'bigquery_producao'
-- 
-- model-paths: ["models"]
-- test-paths: ["tests"]
-- macro-paths: ["macros"]
-- 
-- models:
--   transparencia_br:
--     staging:
--       +materialized: incremental
--       +tags: ["staging"]
--     marts:
--       +materialized: table
--       +tags: ["marts", "producao"]
-- 
-- 
-- COMO RODAR O dbt:
-- 
--   # Instalar
--   pip install dbt-bigquery
-- 
--   # Executar todos os modelos
--   dbt run
-- 
--   # Executar só o modelo final
--   dbt run --select gastos_publicos
-- 
--   # Rodar os testes de qualidade
--   dbt test
-- 
--   # Gerar documentação navegável
--   dbt docs generate
--   dbt docs serve  (abre em http://localhost:8080)
