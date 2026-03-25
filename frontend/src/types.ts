export interface Municipio {
  codigo_ibge: string
  nome_municipio: string
  uf: string
  nome_estado: string | null
  nome_regiao: string | null
  populacao_estimada: number | null
  porte_municipio: string | null
  latitude: number | null
  longitude: number | null
}

export interface GastoPublico {
  id: string
  categoria_origem: string | null
  agente_publico: string | null
  partido: string | null
  tipo_despesa: string | null
  data_empenho: string
  valor_empenhado: number
  favorecido_nome: string
  favorecido_cnpj_cpf: string | null
  elemento_despesa: string | null
  fonte_recurso: string | null
  funcao_governo: string | null
  numero_empenho: string | null
  municipio_ibge: string
  uf: string
  fornecedor_sistema: string | null
  url_origem: string | null
  atualizado_em: string
}

export interface PageMeta {
  page: number
  page_size: number
  total: number
  total_pages: number
}

export interface GastoListResponse {
  items: GastoPublico[]
  meta: PageMeta
}

export interface ResumoGastos {
  total_empenhado: number
  quantidade_registros: number
  ticket_medio: number
}

export interface TopFornecedor {
  favorecido_nome: string
  total_empenhado: number
  quantidade_empenhos: number
}

export interface StatFuncao {
  funcao: string
  total: number
  qtd: number
}

export interface StatUF {
  uf: string
  total: number
  qtd: number
}

export interface StatCategoria {
  categoria: string
  total: number
  qtd: number
}

export interface EvolucaoMensal {
  mes: string
  total: number
  qtd: number
}

export interface GastosFilters {
  page?: number
  page_size?: number
  data_inicio?: string
  data_fim?: string
  uf?: string
  municipio_ibge?: string
  elemento_despesa?: string
  fornecedor?: string
  categoria_origem?: string
  agente_publico?: string
  partido?: string
}
