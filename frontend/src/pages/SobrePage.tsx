import { Github, Globe, Database, Layers, Zap } from 'lucide-react'

export function SobrePage() {
  return (
    <div className="max-w-2xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Sobre o IIIbrasil</h1>
        <p className="text-slate-500 dark:text-slate-400 text-sm mt-1">
          Super-Integrador de Transparência Pública
        </p>
      </div>

      <div className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 p-6 shadow-sm space-y-4">
        <p className="text-slate-700 dark:text-slate-300 leading-relaxed">
          O <strong>IIIbrasil</strong> é uma plataforma open source que coleta, normaliza e serve dados de
          gastos públicos de múltiplas fontes governamentais — Federal, Estadual e Municipal — em um
          <strong> Schema Único</strong>, facilitando análise e fiscalização cidadã.
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {[
            { icon: Database, label: 'Fontes Integradas', desc: 'Câmara, Senado, portais municipais Betha' },
            { icon: Layers, label: 'Schema Único', desc: 'Dados normalizados com código IBGE e UF' },
            { icon: Zap, label: 'Pipeline ETL', desc: 'Apache Airflow + dbt para transformações' },
            { icon: Globe, label: 'API REST', desc: 'FastAPI com filtros avançados e paginação' },
          ].map(({ icon: Icon, label, desc }) => (
            <div key={label} className="flex items-start gap-3 p-3 bg-slate-50 dark:bg-slate-700/40 rounded-xl">
              <Icon size={18} className="text-green-500 mt-0.5 shrink-0" />
              <div>
                <p className="text-sm font-semibold text-slate-800 dark:text-slate-200">{label}</p>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">{desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 p-6 shadow-sm">
        <h2 className="font-semibold text-slate-900 dark:text-white mb-3 text-sm uppercase tracking-wider">
          Tecnologias
        </h2>
        <div className="flex flex-wrap gap-2">
          {['Python', 'FastAPI', 'SQLAlchemy', 'Airflow', 'dbt', 'n8n', 'React', 'TypeScript', 'Vite', 'Tailwind CSS', 'Recharts'].map(t => (
            <span key={t} className="px-2.5 py-1 bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300 text-xs rounded-lg font-medium">
              {t}
            </span>
          ))}
        </div>
      </div>

      <div className="flex items-center gap-3">
        <a
          href="http://localhost:8000/docs"
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 text-white text-sm font-medium rounded-xl transition-colors"
        >
          <Globe size={15} /> API Docs
        </a>
        <a
          href="https://github.com"
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-2 px-4 py-2 bg-slate-100 dark:bg-slate-700 hover:bg-slate-200 dark:hover:bg-slate-600 text-slate-800 dark:text-slate-200 text-sm font-medium rounded-xl transition-colors"
        >
          <Github size={15} /> GitHub
        </a>
      </div>
    </div>
  )
}
