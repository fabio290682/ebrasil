import axios from 'axios'
import type {
  GastoListResponse,
  GastosFilters,
  ResumoGastos,
  TopFornecedor,
  Municipio,
  StatFuncao,
  StatUF,
  StatCategoria,
  EvolucaoMensal,
} from './types'

const api = axios.create({ baseURL: '/api/v1' })

function toParams(obj: Record<string, unknown>) {
  const p: Record<string, string> = {}
  for (const [k, v] of Object.entries(obj)) {
    if (v !== undefined && v !== null && v !== '') p[k] = String(v)
  }
  return p
}

export async function fetchGastos(filters: GastosFilters): Promise<GastoListResponse> {
  const { data } = await api.get('/gastos', { params: toParams(filters as Record<string, unknown>) })
  return data
}

export async function fetchResumo(filters: Omit<GastosFilters, 'page' | 'page_size' | 'elemento_despesa' | 'fornecedor'>): Promise<ResumoGastos> {
  const { data } = await api.get('/gastos/resumo', { params: toParams(filters as Record<string, unknown>) })
  return data
}

export async function fetchTopFornecedores(params: { limit?: number; data_inicio?: string; data_fim?: string; uf?: string; categoria_origem?: string }): Promise<TopFornecedor[]> {
  const { data } = await api.get('/gastos/top-fornecedores', { params: toParams(params as Record<string, unknown>) })
  return data
}

export async function fetchMunicipios(uf?: string): Promise<Municipio[]> {
  const { data } = await api.get('/municipios', { params: uf ? { uf } : {} })
  return data
}

export async function fetchStatsFuncao(params?: { data_inicio?: string; data_fim?: string; uf?: string }): Promise<StatFuncao[]> {
  const { data } = await api.get('/stats/por-funcao', { params: toParams((params ?? {}) as Record<string, unknown>) })
  return data
}

export async function fetchStatsUF(params?: { data_inicio?: string; data_fim?: string }): Promise<StatUF[]> {
  const { data } = await api.get('/stats/por-uf', { params: toParams((params ?? {}) as Record<string, unknown>) })
  return data
}

export async function fetchStatsCategoria(params?: { data_inicio?: string; data_fim?: string; uf?: string }): Promise<StatCategoria[]> {
  const { data } = await api.get('/stats/por-categoria', { params: toParams((params ?? {}) as Record<string, unknown>) })
  return data
}

export async function fetchEvolucaoMensal(params?: { data_inicio?: string; data_fim?: string; uf?: string }): Promise<EvolucaoMensal[]> {
  const { data } = await api.get('/stats/evolucao-mensal', { params: toParams((params ?? {}) as Record<string, unknown>) })
  return data
}
