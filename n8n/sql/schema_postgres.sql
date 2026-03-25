-- Catalogo dinamico de fontes e pipeline nacional
-- Compatível com PostgreSQL/Supabase

CREATE TABLE IF NOT EXISTS fontes_transparencia (
    id BIGSERIAL PRIMARY KEY,
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    nome_fonte TEXT NOT NULL,
    esfera TEXT NOT NULL CHECK (esfera IN ('federal', 'estadual', 'municipal')),
    uf CHAR(2),
    municipio_nome TEXT,
    municipio_ibge CHAR(7),
    sistema_fornecedor TEXT, -- betha, fiorilli, ipm, govbr, etc.
    tipo_coleta TEXT NOT NULL CHECK (tipo_coleta IN ('api_json', 'api_xml', 'html_scraping')),
    metodo_http TEXT NOT NULL DEFAULT 'GET',
    url_base TEXT NOT NULL,
    path_endpoint TEXT,
    query_template JSONB DEFAULT '{}'::jsonb,
    headers_template JSONB DEFAULT '{}'::jsonb,
    auth_tipo TEXT DEFAULT 'none', -- none, api_key, bearer
    auth_segredo_ref TEXT,         -- referência ao segredo no n8n/secret manager
    timeout_ms INTEGER NOT NULL DEFAULT 30000,
    retries INTEGER NOT NULL DEFAULT 2,
    throttle_ms INTEGER NOT NULL DEFAULT 300,
    normalizador_id TEXT NOT NULL DEFAULT 'default_v1',
    mapeamento_campos JSONB DEFAULT '{}'::jsonb,
    status_ultima_coleta TEXT,
    ultima_coleta_em TIMESTAMPTZ,
    ultimo_erro TEXT,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    atualizado_em TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_fontes_ativas ON fontes_transparencia (ativo);
CREATE INDEX IF NOT EXISTS idx_fontes_esfera ON fontes_transparencia (esfera);
CREATE INDEX IF NOT EXISTS idx_fontes_uf ON fontes_transparencia (uf);
CREATE INDEX IF NOT EXISTS idx_fontes_ibge ON fontes_transparencia (municipio_ibge);

CREATE TABLE IF NOT EXISTS gastos_publicos_raw (
    id BIGSERIAL PRIMARY KEY,
    fonte_id BIGINT NOT NULL REFERENCES fontes_transparencia(id),
    payload JSONB NOT NULL,
    coletado_em TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS gastos_publicos_unificados (
    id_transacao TEXT PRIMARY KEY,
    fonte_id BIGINT REFERENCES fontes_transparencia(id),
    categoria_origem TEXT, -- Legislativo Federal, Executivo Federal, etc.
    agente_publico TEXT,   -- Deputado, Senador, Ministro, etc.
    partido TEXT,          -- PL, PT, UNIAO...
    tipo_despesa TEXT,     -- CEAP: combustivel, passagens, divulgacao...
    data_empenho DATE,
    valor_empenhado NUMERIC(18,2) NOT NULL DEFAULT 0,
    favorecido_nome TEXT,
    favorecido_cnpj_cpf TEXT,
    elemento_despesa TEXT,
    fonte_recurso TEXT,
    funcao_governo TEXT,
    numero_empenho TEXT,
    municipio_nome TEXT,
    municipio_ibge CHAR(7),
    uf CHAR(2),
    fornecedor_sistema TEXT,
    url_origem TEXT,
    atualizado_em TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    payload_origem JSONB
);

CREATE INDEX IF NOT EXISTS idx_gastos_data ON gastos_publicos_unificados (data_empenho);
CREATE INDEX IF NOT EXISTS idx_gastos_uf ON gastos_publicos_unificados (uf);
CREATE INDEX IF NOT EXISTS idx_gastos_ibge ON gastos_publicos_unificados (municipio_ibge);
CREATE INDEX IF NOT EXISTS idx_gastos_valor ON gastos_publicos_unificados (valor_empenhado);
CREATE INDEX IF NOT EXISTS idx_gastos_categoria ON gastos_publicos_unificados (categoria_origem);
CREATE INDEX IF NOT EXISTS idx_gastos_agente ON gastos_publicos_unificados (agente_publico);
CREATE INDEX IF NOT EXISTS idx_gastos_partido ON gastos_publicos_unificados (partido);

-- UPSERT helper: para uso no nó SQL do n8n
-- ON CONFLICT (id_transacao) DO UPDATE SET atualizado_em = NOW(), ...
