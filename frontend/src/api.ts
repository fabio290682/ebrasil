import type {
  EvolucaoMensal,
  Gasto,
  GastosFilters,
  Meta,
  Municipio,
  Resumo,
  StatsFuncao,
  TopFornecedor,
} from './types'

const TIMEOUT_MS = 15_000

function normalizeBaseUrl(value: string): string {
  const trimmed = String(value || '').trim().replace(/\/+$/, '')
  if (!trimmed) return '/api/v1'
  if (/^https?:\/\/[^/]+$/i.test(trimmed)) return `${trimmed}/api/v1`
  return trimmed
}

const BASE_URL = normalizeBaseUrl(import.meta.env.VITE_API_BASE_URL || '')
const IS_ABSOLUTE = /^https?:\/\//i.test(BASE_URL)

async function request<T>(path: string, params?: Record<string, unknown>): Promise<T> {
  const fullPath = `${BASE_URL}${path}`
  const url = IS_ABSOLUTE
    ? new URL(fullPath)
    : new URL(fullPath, window.location.origin)

  if (params) {
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== '') {
        url.searchParams.append(k, String(v))
      }
    })
  }

  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS)

  try {
    const res = await fetch(url.toString(), { signal: controller.signal })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    return res.json() as Promise<T>
  } finally {
    clearTimeout(timer)
  }
}

export const fetchGastos = (filters: GastosFilters) =>
  request<{ items: Gasto[]; meta: Meta }>('/gastos', filters as Record<string, unknown>)

export const fetchMunicipios = (uf?: string) =>
  request<Municipio[]>('/municipios', { uf })

export const fetchResumo = (filters: Partial<GastosFilters>) =>
  request<Resumo>('/gastos/resumo', filters as Record<string, unknown>)

export const fetchTopFornecedores = (params: { limit?: number }) =>
  request<TopFornecedor[]>('/gastos/top-fornecedores', params)

export const fetchStatsFuncao = () =>
  request<StatsFuncao[]>('/gastos/stats/funcao')

export const fetchStatsCategoria = () =>
  request<{ categoria: string; total: number }[]>('/gastos/stats/categoria')

export const fetchEvolucaoMensal = () =>
  request<EvolucaoMensal[]>('/gastos/stats/evolucao')
