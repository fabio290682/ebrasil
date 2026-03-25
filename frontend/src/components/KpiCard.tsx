import type { ReactNode } from 'react'

interface Props {
  title: string
  value: string
  sub?: string
  icon: ReactNode
  color?: string
}

export function KpiCard({ title, value, sub, icon, color = 'text-emerald-500' }: Props) {
  return (
    <div className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 p-5 flex items-start gap-4 shadow-sm">
      <div className={`p-3 rounded-xl bg-slate-100 dark:bg-slate-700 ${color}`}>{icon}</div>
      <div className="min-w-0">
        <p className="text-sm text-slate-500 dark:text-slate-400 font-medium">{title}</p>
        <p className="text-2xl font-bold text-slate-900 dark:text-white leading-tight mt-0.5 truncate">{value}</p>
        {sub && <p className="text-xs text-slate-400 mt-1">{sub}</p>}
      </div>
    </div>
  )
}
