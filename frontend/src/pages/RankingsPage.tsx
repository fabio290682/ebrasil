import { useQuery } from '@tanstack/react-query'
import { Trophy, TrendingDown } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { fetchTopFornecedores, fetchStatsFuncao, fetchStatsCategoria } from '../api'
import { Spinner } from '../components/Spinner'
import { formatBRL, shortBRL } from '../utils'

export function RankingsPage() {
  const { data: topForn, isLoading: l1 } = useQuery({ queryKey: ['top-forn-50'], queryFn: () => fetchTopFornecedores({ limit: 15 }) })
  const { data: funcao, isLoading: l2 } = useQuery({ queryKey: ['stats-funcao-full'], queryFn: () => fetchStatsFuncao() })
  const { data: categoria } = useQuery({ queryKey: ['stats-categoria'], queryFn: () => fetchStatsCategoria() })

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Rankings</h1>
        <p className="text-slate-500 dark:text-slate-400 text-sm mt-1">Maiores fornecedores e distribuição de gastos</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 p-5 shadow-sm">
          <h2 className="font-semibold text-slate-900 dark:text-white mb-4 flex items-center gap-2">
            <Trophy size={16} className="text-yellow-500" /> Top 15 Fornecedores
          </h2>
          {l1 ? <div className="flex justify-center py-8"><Spinner /></div> : (
            <>
              <ResponsiveContainer width="100%" height={320}>
                <BarChart data={topForn} layout="vertical" margin={{ left: 4, right: 16 }}>
                  <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#e2e8f0" />
                  <XAxis type="number" tickFormatter={shortBRL} tick={{ fontSize: 10 }} />
                  <YAxis
                    dataKey="favorecido_nome"
                    type="category"
                    width={130}
                    tick={{ fontSize: 10 }}
                    tickFormatter={(v: string) => v.length > 20 ? v.slice(0, 20) + '…' : v}
                  />
                  <Tooltip formatter={(v: number) => formatBRL(v)} />
                  <Bar dataKey="total_empenhado" fill="#10b981" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
              <div className="mt-4 space-y-2 max-h-48 overflow-y-auto">
                {(topForn ?? []).map((f, i) => (
                  <div key={f.favorecido_nome} className="flex items-center justify-between py-1.5 px-3 bg-slate-50 dark:bg-slate-700/40 rounded-lg">
                    <div className="flex items-center gap-2 min-w-0">
                      <span className="text-xs font-bold text-slate-400 w-5 shrink-0">#{i + 1}</span>
                      <span className="text-sm text-slate-800 dark:text-slate-200 truncate">{f.favorecido_nome}</span>
                    </div>
                    <div className="text-right shrink-0 ml-4">
                      <p className="text-sm font-semibold text-slate-900 dark:text-white">{shortBRL(f.total_empenhado)}</p>
                      <p className="text-xs text-slate-400">{f.quantidade_empenhos} empenhos</p>
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>

        <div className="space-y-4">
          <div className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 p-5 shadow-sm">
            <h2 className="font-semibold text-slate-900 dark:text-white mb-4 flex items-center gap-2">
              <TrendingDown size={16} className="text-blue-500" /> Por Função de Governo
            </h2>
            {l2 ? <div className="flex justify-center py-8"><Spinner /></div> : (
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={funcao}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="funcao" tick={{ fontSize: 10 }} tickFormatter={(v: string) => v.length > 10 ? v.slice(0, 10) + '…' : v} />
                  <YAxis tickFormatter={shortBRL} tick={{ fontSize: 10 }} />
                  <Tooltip formatter={(v: number) => formatBRL(v)} />
                  <Bar dataKey="total" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>

          <div className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 p-5 shadow-sm">
            <h2 className="font-semibold text-slate-900 dark:text-white mb-3">Por Categoria</h2>
            <div className="space-y-2">
              {(categoria ?? []).map((c, i) => {
                const max = (categoria ?? [])[0]?.total ?? 1
                return (
                  <div key={c.categoria}>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-slate-700 dark:text-slate-300 truncate max-w-[60%]">{c.categoria}</span>
                      <span className="font-semibold text-slate-900 dark:text-white">{shortBRL(c.total)}</span>
                    </div>
                    <div className="h-1.5 bg-slate-100 dark:bg-slate-700 rounded-full overflow-hidden">
                      <div
                        className="h-full rounded-full"
                        style={{ width: `${(c.total / max) * 100}%`, background: ['#10b981','#3b82f6','#8b5cf6','#f59e0b','#ef4444'][i % 5] }}
                      />
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
