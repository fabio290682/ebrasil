﻿import { useQuery } from '@tanstack/react-query'
import { DollarSign, Hash, TrendingUp, Building2 } from 'lucide-react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  LineChart, Line, PieChart, Pie, Cell, Legend,
} from 'recharts'
import { KpiCard } from '../components/KpiCard'
import { Spinner } from '../components/Spinner'
import { fetchResumo, fetchTopFornecedores, fetchStatsFuncao, fetchEvolucaoMensal } from '../api'
import { formatBRL, shortBRL, formatNumber } from '../utils'

const COLORS = ['#10b981', '#3b82f6', '#8b5cf6', '#f59e0b', '#ef4444', '#06b6d4', '#ec4899', '#84cc16']

export function DashboardPage() {
  const { data: resumo, isLoading: loadResumo } = useQuery({ queryKey: ['resumo'], queryFn: () => fetchResumo({}) })
  const { data: topForn } = useQuery({ queryKey: ['top-forn'], queryFn: () => fetchTopFornecedores({ limit: 8 }) })
  const { data: statsFuncao } = useQuery({ queryKey: ['stats-funcao'], queryFn: () => fetchStatsFuncao() })
  const { data: evolucao } = useQuery({ queryKey: ['evolucao'], queryFn: () => fetchEvolucaoMensal() })

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Dashboard</h1>
        <p className="text-slate-500 dark:text-slate-400 text-sm mt-1">Visão geral dos gastos públicos integrados</p>
      </div>

      {loadResumo ? (
        <div className="flex justify-center py-8"><Spinner size={32} /></div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <KpiCard
            title="Total Empenhado"
            value={shortBRL(resumo?.total_empenhado ?? 0)}
            sub={formatBRL(resumo?.total_empenhado ?? 0)}
            icon={<DollarSign size={20} />}
            color="text-emerald-500"
          />
          <KpiCard
            title="Registros"
            value={formatNumber(resumo?.quantidade_registros ?? 0)}
            sub="empenhos consolidados"
            icon={<Hash size={20} />}
            color="text-blue-500"
          />
          <KpiCard
            title="Ticket Médio"
            value={shortBRL(resumo?.ticket_medio ?? 0)}
            sub="por empenho"
            icon={<TrendingUp size={20} />}
            color="text-purple-500"
          />
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 p-5 shadow-sm">
          <h2 className="font-semibold text-slate-900 dark:text-white mb-4 flex items-center gap-2">
            <Building2 size={16} className="text-green-500" /> Top Fornecedores
          </h2>
          {topForn && topForn.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={topForn} layout="vertical" margin={{ left: 0, right: 16 }}>
                <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#e2e8f0" />
                <XAxis type="number" tickFormatter={shortBRL} tick={{ fontSize: 11 }} />
                <YAxis
                  dataKey="favorecido_nome"
                  type="category"
                  width={120}
                  tick={{ fontSize: 10 }}
                  tickFormatter={(v: string) => v.length > 18 ? v.slice(0, 18) + '…' : v}
                />
                <Tooltip formatter={(v: number) => formatBRL(v)} />
                <Bar dataKey="total_empenhado" fill="#10b981" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : <div className="flex justify-center py-8"><Spinner /></div>}
        </div>

        <div className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 p-5 shadow-sm">
          <h2 className="font-semibold text-slate-900 dark:text-white mb-4">Gastos por Função</h2>
          {statsFuncao && statsFuncao.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie
                  data={statsFuncao}
                  dataKey="total"
                  nameKey="funcao"
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  label={({ funcao, percent }: { funcao: string; percent: number }) =>
                    `${funcao.slice(0, 10)} ${(percent * 100).toFixed(0)}%`
                  }
                  labelLine={false}
                >
                  {statsFuncao.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Pie>
                <Tooltip formatter={(v: number) => formatBRL(v)} />
                <Legend formatter={(v: string) => v.length > 14 ? v.slice(0, 14) + '…' : v} />
              </PieChart>
            </ResponsiveContainer>
          ) : <div className="flex justify-center py-8"><Spinner /></div>}
        </div>
      </div>

      {evolucao && evolucao.length > 0 && (
        <div className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 p-5 shadow-sm">
          <h2 className="font-semibold text-slate-900 dark:text-white mb-4">Evolução Mensal</h2>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={evolucao}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="mes" tick={{ fontSize: 12 }} />
              <YAxis tickFormatter={shortBRL} tick={{ fontSize: 11 }} />
              <Tooltip formatter={(v: number) => formatBRL(v)} />
              <Line type="monotone" dataKey="total" stroke="#10b981" strokeWidth={2} dot={{ r: 4 }} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  )
}
