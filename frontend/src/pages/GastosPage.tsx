import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Search, ChevronLeft, ChevronRight, ExternalLink, Download, XCircle, Landmark, History, ShieldCheck } from 'lucide-react'
import { fetchGastos, fetchMunicipios, fetchResumo } from '../api'
import { Spinner } from '../components/Spinner'
import { Badge } from '../components/Badge'
import { formatBRL, formatDate } from '../utils'
import type { GastosFilters } from '../types'

const UFS = ['AC','AL','AM','AP','BA','CE','DF','ES','GO','MA','MG','MS','MT','PA','PB','PE','PI','PR','RJ','RN','RO','RR','RS','SC','SE','SP','TO']

export function GastosPage() {
  const [filters, setFilters] = useState<GastosFilters>({ page: 1, page_size: 20 })
  const [draft, setDraft] = useState<GastosFilters>({})
  const [showAudit, setShowAudit] = useState(false)

  const { data, isLoading } = useQuery({
    queryKey: ['gastos', filters],
    queryFn: () => fetchGastos(filters),
  })

  const { data: resumoLeg } = useQuery({
    queryKey: ['resumo-legislativo'],
    queryFn: () => fetchResumo({ categoria_origem: 'Legislativo Federal' }),
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

  function handleExport() {
    const params = new URLSearchParams()
    Object.entries(filters).forEach(([key, value]) => {
      if (value) params.append(key, String(value))
    })
    // Remove paginação para exportar o lote completo
    params.delete('page')
    params.delete('page_size')
    const rawBase = import.meta.env.VITE_API_BASE_URL || '/api/v1'
    const baseUrl = rawBase.replace(/\/+$/, '')
    const isAbsolute = /^https?:\/\//i.test(baseUrl)
    const exportUrl = isAbsolute
      ? new URL(`${baseUrl}/gastos/export/csv?${params.toString()}`)
      : new URL(`${baseUrl}/gastos/export/csv?${params.toString()}`, window.location.origin)
    window.open(exportUrl.toString(), '_blank')
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

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white dark:bg-slate-800 p-5 rounded-2xl border border-slate-200 dark:border-slate-700 shadow-sm">
          <div className="flex items-center justify-between mb-3">
            <span className="text-sm font-medium text-slate-500 dark:text-slate-400">Cota Parlamentar (Mês)</span>
            <div className="p-2 bg-orange-100 dark:bg-orange-900/30 rounded-xl">
              <Landmark size={20} className="text-orange-600" />
            </div>
          </div>
          <div className="space-y-1">
            <div className="text-3xl font-bold text-slate-900 dark:text-white" id="kpi-cota-parlamentar">
              {resumoLeg ? formatBRL(resumoLeg.total_empenhado ?? 0) : 'R$ 0,00'}
            </div>
            <div className="text-xs text-slate-400 flex items-center gap-1">
              <span className="text-orange-500 font-medium">-</span> Deputados e Senadores
            </div>
          </div>
        </div>
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
          <div>
            <label className="text-xs font-medium text-slate-600 dark:text-slate-400 mb-1 block">Poder / Categoria</label>
            <select
              className="w-full px-3 py-2 text-sm bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 dark:text-white"
              value={draft.categoria_origem ?? ''}
              onChange={e => setDraft(d => ({ ...d, categoria_origem: e.target.value || undefined }))}
            >
              <option value="">Todos os Poderes</option>
              <option value="Executivo Federal">Executivo (Ministérios)</option>
              <option value="Legislativo Federal">Legislativo (Deputados e Senadores)</option>
              <option value="Judiciário">Judiciário</option>
            </select>
          </div>
          <div className="flex items-end gap-2">
            <button
              onClick={applyFilters}
              className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 text-white text-sm font-medium rounded-lg transition-colors cursor-pointer"
            >
              <Search size={14} /> Filtrar
            </button>
            <button
              onClick={handleExport}
              title="Exportar CSV"
              className="px-3 py-2 bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-600 transition-colors cursor-pointer"
            >
              <Download size={14} />
            </button>
            <button
              onClick={() => setShowAudit(true)}
              title="Log de Auditoria"
              className="px-3 py-2 bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-600 transition-colors cursor-pointer"
            >
              <History size={14} />
            </button>
            <button
              onClick={clearFilters}
              className="px-3 py-2 text-slate-400 hover:text-rose-500 transition-colors cursor-pointer"
              title="Limpar filtros"
            >
              <XCircle size={18} />
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
                  {['Data', 'Favorecido', 'Poder', 'Valor', 'UF', 'Origem', 'Ações'].map(h => (
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
                      <div className="flex items-center gap-1">
                        {g.agente_publico && <span className="text-xs text-slate-400 truncate">{g.agente_publico}</span>}
                        {g.partido && <span className="text-[10px] font-bold text-slate-400 uppercase">[{g.partido}]</span>}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-slate-600 dark:text-slate-400 whitespace-nowrap">
                      {g.categoria_origem ? (
                        <Badge label={g.categoria_origem} variant="green" />
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

      {/* Modal de Auditoria de Exportação */}
      {showAudit && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm">
          <div className="bg-white dark:bg-slate-800 w-full max-w-lg rounded-2xl shadow-2xl border border-slate-200 dark:border-slate-700 overflow-hidden animate-in fade-in zoom-in duration-200">
            <div className="px-6 py-4 border-b border-slate-100 dark:border-slate-700 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <ShieldCheck className="text-green-600" size={20} />
                <h2 className="font-bold text-slate-900 dark:text-white">Log de Auditoria</h2>
              </div>
              <button onClick={() => setShowAudit(false)} className="text-slate-400 hover:text-slate-600 transition-colors">
                <XCircle size={20} />
              </button>
            </div>
            <div className="p-6 max-h-[400px] overflow-y-auto space-y-4">
              <p className="text-xs text-slate-500 uppercase font-semibold tracking-wider">Registros recentes de exportação</p>
              <div className="space-y-3">
                {/* Em um cenário real, estes dados viriam de uma useQuery para fetchAuditLogs */}
                {[1, 2, 3].map(i => (
                  <div key={i} className="flex items-start justify-between p-3 bg-slate-50 dark:bg-slate-700/40 rounded-xl border border-slate-100 dark:border-slate-600">
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-slate-800 dark:text-slate-200 truncate">Relatório de Gastos (CSV)</p>
                      <p className="text-xs text-slate-500">Usuário: gestor_dados@ebrasil.gov.br</p>
                      <p className="text-[10px] text-slate-400 mt-1 italic">Origem: IP 189.12.{i}.145 • Filtros Aplicados</p>
                    </div>
                    <span className="text-[10px] font-mono text-slate-400 bg-slate-100 dark:bg-slate-700 px-1.5 py-0.5 rounded shrink-0">14/10 10:4{i}</span>
                  </div>
                ))}
              </div>
            </div>
            <div className="px-6 py-4 bg-slate-50 dark:bg-slate-800/50 border-t border-slate-100 dark:border-slate-700 flex justify-end">
              <button onClick={() => setShowAudit(false)} className="px-4 py-2 bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-200 text-sm font-medium rounded-lg hover:bg-slate-300 dark:hover:bg-slate-600 transition-colors">
                Fechar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
