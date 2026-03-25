export interface Gasto {
  id: string
  data_empenho: string
  favorecido_nome: string
  agente_publico?: string
  funcao_governo?: string
  valor_empenhado: number
  uf: string
  fornecedor_sistema?: string
  url_origem?: string
  municipio_ibge?: string
  partido?: string
}

export interface Meta {
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface GastosFilters {
  page?: number
  page_size?: number
  fornecedor?: string
  agente_publico?: string
  uf?: string
  municipio_ibge?: string
  data_inicio?: string
  data_fim?: string
  partido?: string
}

export interface Municipio {
  codigo_ibge: string
  nome_municipio: string
  uf: string
}

export interface Resumo {
  total_empenhado: number
  quantidade_registros: number
  ticket_medio: number
}

export interface TopFornecedor {
  favorecido_nome: string
  total_empenhado: number
  quantidade_empenhos: number
}

export interface StatsFuncao {
  funcao: string
  total: number
}

export interface EvolucaoMensal {
  mes: string
  total: number
}