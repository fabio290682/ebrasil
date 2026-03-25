import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Search, ChevronLeft, ChevronRight, ExternalLink } from 'lucide-react'
import { fetchGastos, fetchMunicipios } from '../api'
import { Spinner } from '../components/Spinner'
import { Badge } from '../components/Badge'
import { formatBRL, formatDate } from '../utils'
import type { GastosFilters } from '../types'

const UFS = ['AC','AL','AM','AP','BA','CE','DF','ES','GO','MA','MG','MS','MT','PA','PB','PE','PI','PR','RJ','RN','RO','RR','RS','SC','SE','SP','TO']

export function GastosPage() {
  const [filters, setFilters] = useState<GastosFilters>({ page: 1, page_size: 20 })
  const [draft, setDraft] = useState<GastosFilters>({})

  const { data, isLoading } = useQuery({
    queryKey: ['gastos', filters],
    queryFn: () => fetchGastos(filters),
  })

  const { data: municipios } = useQuery({
    queryKey: ['municipios', draft.uf],
    queryFn: () => fetchMunicipios(draft.uf),
    enabled: !!draft.uf,
  })

  function applyFilters() {
    setFilters({ ...draft, page: 1, page_size: 20 })
  }

  function clearFilters() {
    setDraft({})
    setFilters({ page: 1, page_size: 20 })
  }

  function setPage(p: number) {
    setFilters(f => ({ ...f, page: p }))
  }

  const meta = data?.meta
  const items = data?.items ?? []

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Gastos Públicos</h1>
        <p className="text-slate-500 dark:text-slate-400 text-sm mt-1">Pesquise e filtre empenhos consolidados</p>
      </div>

      <div className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 p-4 shadow-sm">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
          <div>
            <label className="text-xs font-medium text-slate-600 dark:text-slate-400 mb-1 block">Fornecedor</label>
            <input
              className="w-full px-3 py-2 text-sm bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 dark:text-white"
              placeholder="Nome do fornecedor"
              value={draft.fornecedor ?? ''}
              onChange={e => setDraft(d => ({ ...d, fornecedor: e.target.value }))}
            />
          </div>
          <div>
            <label className="text-xs font-medium text-slate-600 dark:text-slate-400 mb-1 block">Agente Público</label>
            <input
              className="w-full px-3 py-2 text-sm bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 dark:text-white"
              placeholder="Nome do agente"
              value={draft.agente_publico ?? ''}
              onChange={e => setDraft(d => ({ ...d, agente_publico: e.target.value }))}
            />
          </div>
          <div>
            <label className="text-xs font-medium text-slate-600 dark:text-slate-400 mb-1 block">UF</label>
            <select
              className="w-full px-3 py-2 text-sm bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 dark:text-white"
              value={draft.uf ?? ''}
              onChange={e => setDraft(d => ({ ...d, uf: e.target.value || undefined, municipio_ibge: undefined }))}
            >
              <option value="">Todos os estados</option>
              {UFS.map(uf => <option key={uf} value={uf}>{uf}</option>)}
            </select>
          </div>
          <div>
            <label className="text-xs font-medium text-slate-600 dark:text-slate-400 mb-1 block">Município</label>
            <select
              className="w-full px-3 py-2 text-sm bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 dark:text-white disabled:opacity-50"
              value={draft.municipio_ibge ?? ''}
              onChange={e => setDraft(d => ({ ...d, municipio_ibge: e.target.value || undefined }))}
              disabled={!draft.uf}
            >
              <option value="">{draft.uf ? 'Todos' : 'Selecione UF'}</option>
              {(municipios ?? []).map(m => <option key={m.codigo_ibge} value={m.codigo_ibge}>{m.nome_municipio}</option>)}
            </select>
          </div>
          <div>
            <label className="text-xs font-medium text-slate-600 dark:text-slate-400 mb-1 block">Data início</label>
            <input
              type="date"
              className="w-full px-3 py-2 text-sm bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 dark:text-white"
              value={draft.data_inicio ?? ''}
              onChange={e => setDraft(d => ({ ...d, data_inicio: e.target.value || undefined }))}
            />
          </div>
          <div>
            <label className="text-xs font-medium text-slate-600 dark:text-slate-400 mb-1 block">Data fim</label>
            <input
              type="date"
              className="w-full px-3 py-2 text-sm bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 dark:text-white"
              value={draft.data_fim ?? ''}
              onChange={e => setDraft(d => ({ ...d, data_fim: e.target.value || undefined }))}
            />
          </div>
          <div>
            <label className="text-xs font-medium text-slate-600 dark:text-slate-400 mb-1 block">Partido</label>
            <input
              className="w-full px-3 py-2 text-sm bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 dark:text-white"
              placeholder="Ex: PT, PL..."
              value={draft.partido ?? ''}
              onChange={e => setDraft(d => ({ ...d, partido: e.target.value || undefined }))}
            />
          </div>
          <div className="flex items-end gap-2">
            <button
              onClick={applyFilters}
              className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 text-white text-sm font-medium rounded-lg transition-colors cursor-pointer"
            >
              <Search size={14} /> Filtrar
            </button>
            <button
              onClick={clearFilters}
              className="px-3 py-2 text-sm text-slate-500 hover:text-slate-700 dark:hover:text-slate-300 border border-slate-200 dark:border-slate-600 rounded-lg transition-colors cursor-pointer"
            >
              Limpar
            </button>
          </div>
        </div>
      </div>

      <div className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 shadow-sm overflow-hidden">
        <div className="px-5 py-3 border-b border-slate-100 dark:border-slate-700 flex items-center justify-between">
          <span className="text-sm font-medium text-slate-700 dark:text-slate-300">
            {meta ? `${meta.total.toLocaleString('pt-BR')} registros encontrados` : 'Carregando...'}
          </span>
          {meta && (
            <span className="text-xs text-slate-400">
              Página {meta.page} de {meta.total_pages}
            </span>
          )}
        </div>

        {isLoading ? (
          <div className="flex justify-center py-12"><Spinner size={32} /></div>
        ) : items.length === 0 ? (
          <div className="py-12 text-center text-slate-400 text-sm">Nenhum registro encontrado.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-slate-50 dark:bg-slate-700/50">
                  {['Data', 'Favorecido', 'Função', 'Valor', 'UF', 'Origem', 'Ações'].map(h => (
                    <th key={h} className="text-left px-4 py-3 text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider whitespace-nowrap">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-700">
                {items.map(g => (
                  <tr key={g.id} className="hover:bg-slate-50 dark:hover:bg-slate-700/30 transition-colors">
                    <td className="px-4 py-3 text-slate-600 dark:text-slate-400 whitespace-nowrap">{formatDate(g.data_empenho)}</td>
                    <td className="px-4 py-3 max-w-[200px]">
                      <div className="font-medium text-slate-800 dark:text-slate-200 truncate">{g.favorecido_nome}</div>
                      {g.agente_publico && <div className="text-xs text-slate-400 truncate">{g.agente_publico}</div>}
                    </td>
                    <td className="px-4 py-3 text-slate-600 dark:text-slate-400 whitespace-nowrap">
                      {g.funcao_governo ? (
                        <Badge label={g.funcao_governo} variant="green" />
                      ) : '—'}
                    </td>
                    <td className="px-4 py-3 font-semibold text-slate-900 dark:text-white whitespace-nowrap">
                      {formatBRL(g.valor_empenhado)}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      <Badge label={g.uf} variant="blue" />
                    </td>
                    <td className="px-4 py-3 text-slate-500 dark:text-slate-400 whitespace-nowrap text-xs">
                      {g.fornecedor_sistema ?? '—'}
                    </td>
                    <td className="px-4 py-3">
                      {g.url_origem ? (
                        <a href={g.url_origem} target="_blank" rel="noopener noreferrer"
                          className="text-green-600 hover:text-green-700">
                          <ExternalLink size={14} />
                        </a>
                      ) : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {meta && meta.total_pages > 1 && (
          <div className="px-5 py-3 border-t border-slate-100 dark:border-slate-700 flex items-center justify-between">
            <button
              disabled={meta.page <= 1}
              onClick={() => setPage(meta.page - 1)}
              className="flex items-center gap-1 px-3 py-1.5 text-sm border border-slate-200 dark:border-slate-600 rounded-lg disabled:opacity-40 cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors"
            >
              <ChevronLeft size={14} /> Anterior
            </button>
            <span className="text-sm text-slate-500">
              {meta.page} / {meta.total_pages}
            </span>
            <button
              disabled={meta.page >= meta.total_pages}
              onClick={() => setPage(meta.page + 1)}
              className="flex items-center gap-1 px-3 py-1.5 text-sm border border-slate-200 dark:border-slate-600 rounded-lg disabled:opacity-40 cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors"
            >
              Próxima <ChevronRight size={14} />
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
