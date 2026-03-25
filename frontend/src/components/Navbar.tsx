import { BarChart3, Search, Home, FileText, Map, Sun, Moon } from 'lucide-react'
import { useDarkMode } from '../hooks/useDarkMode'

interface Props {
  active: string
  onChange: (tab: string) => void
}

const TABS = [
  { id: 'dashboard', label: 'Dashboard', icon: Home },
  { id: 'gastos', label: 'Gastos', icon: Search },
  { id: 'rankings', label: 'Rankings', icon: BarChart3 },
  { id: 'mapa', label: 'Por Estado', icon: Map },
  { id: 'sobre', label: 'Sobre', icon: FileText },
]

export function Navbar({ active, onChange }: Props) {
  const [isDark, setIsDark] = useDarkMode()

  return (
    <header className="bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 sticky top-0 z-50 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 bg-gradient-to-br from-green-500 to-blue-600 rounded-xl flex items-center justify-center shadow">
              <span className="text-white font-bold text-sm">III</span>
            </div>
            <div>
              <span className="font-bold text-slate-900 dark:text-white text-lg leading-none">IIIbrasil</span>
              <p className="text-[10px] text-slate-400 leading-none mt-0.5">Transparência Pública</p>
            </div>
          </div>
          <nav className="hidden md:flex items-center gap-1">
            {TABS.map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                onClick={() => onChange(id)}
                className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors cursor-pointer ${
                  active === id
                    ? 'bg-green-50 dark:bg-green-900/30 text-green-700 dark:text-green-400'
                    : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800'
                }`}
              >
                <Icon size={15} />
                {label}
              </button>
            ))}
          </nav>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setIsDark(!isDark)}
              className="p-2 rounded-lg text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors cursor-pointer"
              title={isDark ? 'Ativar modo claro' : 'Ativar modo escuro'}
            >
              {isDark ? <Sun size={18} /> : <Moon size={18} />}
            </button>

            <div className="flex md:hidden gap-1">
              {TABS.map(({ id, icon: Icon }) => (
                <button
                  key={id}
                  onClick={() => onChange(id)}
                  className={`p-2 rounded-lg transition-colors cursor-pointer ${
                    active === id ? 'text-green-600' : 'text-slate-400'
                  }`}
                >
                  <Icon size={18} />
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </header>
  )
}
