import type { GastosFilters, Gasto, Meta, Municipio, Resumo, TopFornecedor, StatsFuncao, EvolucaoMensal } from './types'

function normalizeBaseUrl(value: string) {
  const trimmed = String(value || '').trim().replace(/\/+$/, '')
  if (!trimmed) return '/api/v1'

  // If an absolute URL was provided without a path, assume the API prefix.
  // Example: https://my-backend.onrender.com  -> https://my-backend.onrender.com/api/v1
  if (/^https?:\/\/[^/]+$/i.test(trimmed)) return `${trimmed}/api/v1`

  return trimmed
}

const BASE_URL = normalizeBaseUrl(import.meta.env.VITE_API_BASE_URL || '/api/v1')
const IS_ABSOLUTE_BASE = /^https?:\/\//i.test(BASE_URL)

async function request<T>(path: string, params?: Record<string, any>): Promise<T> {
  const fullPath = `${BASE_URL}${path}`
  const url = IS_ABSOLUTE_BASE ? new URL(fullPath) : new URL(fullPath, window.location.origin)
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        url.searchParams.append(key, String(value))
      }
    })
  }
  const response = await fetch(url.toString())
  if (!response.ok) throw new Error('Falha na requisição')
  return response.json()
}

export const fetchGastos = (filters: GastosFilters) => 
  request<{ items: Gasto[]; meta: Meta }>('/gastos', filters)

export const fetchMunicipios = (uf?: string) => 
  request<Municipio[]>('/municipios', { uf })

export const fetchResumo = (filters: any) => 
  request<Resumo>('/gastos/resumo', filters)

export const fetchTopFornecedores = (params: { limit?: number }) => 
  request<TopFornecedor[]>('/gastos/top-fornecedores', params)

export const fetchStatsFuncao = () => 
  request<StatsFuncao[]>('/gastos/stats/funcao')

export const fetchStatsCategoria = () => 
  request<{ categoria: string; total: number }[]>('/gastos/stats/categoria')

export const fetchEvolucaoMensal = () => 
  request<EvolucaoMensal[]>('/gastos/stats/evolucao')
