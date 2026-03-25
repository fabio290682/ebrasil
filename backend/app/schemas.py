from datetime import date, datetime

from pydantic import BaseModel, Field


class MunicipioOut(BaseModel):
    codigo_ibge: str = Field(min_length=7, max_length=7)
    nome_municipio: str
    uf: str
    nome_estado: str | None = None
    nome_regiao: str | None = None
    populacao_estimada: int | None = None
    porte_municipio: str | None = None
    latitude: float | None = None
    longitude: float | None = None

    model_config = {"from_attributes": True}


class GastoPublicoOut(BaseModel):
    id: str
    categoria_origem: str | None = None
    agente_publico: str | None = None
    partido: str | None = None
    tipo_despesa: str | None = None
    data_empenho: date
    valor_empenhado: float
    favorecido_nome: str
    favorecido_cnpj_cpf: str | None = None
    elemento_despesa: str | None = None
    fonte_recurso: str | None = None
    funcao_governo: str | None = None
    numero_empenho: str | None = None
    municipio_ibge: str
    uf: str
    fornecedor_sistema: str | None = None
    url_origem: str | None = None
    atualizado_em: datetime

    model_config = {"from_attributes": True}


class PageMeta(BaseModel):
    page: int
    page_size: int
    total: int
    total_pages: int


class GastoListResponse(BaseModel):
    items: list[GastoPublicoOut]
    meta: PageMeta


class ResumoGastosResponse(BaseModel):
    total_empenhado: float
    quantidade_registros: int
    ticket_medio: float


class TopFornecedorItem(BaseModel):
    favorecido_nome: str
    total_empenhado: float
    quantidade_empenhos: int
