import { useEffect, useMemo, useState } from 'react'
import './App.css'

type TabId = 'dashboard' | 'gastos' | 'insights' | 'sobre'

type GastoItem = {
  id?: number
  data_empenho?: string
  favorecido_nome?: string
  funcao_governo?: string
  valor_empenhado?: number
  uf?: string
}

type GastoApiResponse = {
  items?: GastoItem[]
  meta?: {
    total?: number
    page?: number
    total_pages?: number
  }
}

type ResumoResponse = {
  total_empenhado?: number
  quantidade_registros?: number
  ticket_medio?: number
}

const FALLBACK_GASTOS: GastoItem[] = [
  { data_empenho: '2026-03-21', favorecido_nome: 'Construtora Norte', funcao_governo: 'Infraestrutura', valor_empenhado: 185900, uf: 'CE' },
  { data_empenho: '2026-03-20', favorecido_nome: 'Clinica Vida Nova', funcao_governo: 'Saude', valor_empenhado: 76820, uf: 'SP' },
  { data_empenho: '2026-03-20', favorecido_nome: 'Tech Educacional Ltda', funcao_governo: 'Educacao', valor_empenhado: 124000, uf: 'PE' },
  { data_empenho: '2026-03-19', favorecido_nome: 'Servicos Urbanos SA', funcao_governo: 'Administracao', valor_empenhado: 58300, uf: 'MG' },
]

const TABS: { id: TabId; label: string }[] = [
  { id: 'dashboard', label: 'Dashboard' },
  { id: 'gastos', label: 'Gastos' },
  { id: 'insights', label: 'Insights' },
  { id: 'sobre', label: 'Sobre' },
]

const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/+$/, '')
function apiPath(path: string) {
  if (!API_BASE) return path
  return `${API_BASE}${path}`
}

function formatBRL(value: number) {
  return value.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
}

function shortNumber(value: number) {
  return value.toLocaleString('pt-BR')
}

function formatDate(value?: string) {
  if (!value) return '-'
  const date = new Date(`${value}T00:00:00`)
  return Number.isNaN(date.getTime()) ? '-' : date.toLocaleDateString('pt-BR')
}

function calcByCategory(rows: GastoItem[]) {
  const groups: Record<string, number> = {}
  for (const row of rows) {
    const key = row.funcao_governo || 'Outros'
    groups[key] = (groups[key] || 0) + Number(row.valor_empenhado || 0)
  }
  return Object.entries(groups)
    .map(([name, total]) => ({ name, total }))
    .sort((a, b) => b.total - a.total)
}

function App() {
  const [tab, setTab] = useState<TabId>('dashboard')
  const [status, setStatus] = useState<'loading' | 'ready' | 'fallback'>('loading')
  const [gastos, setGastos] = useState<GastoItem[]>([])
  const [resumo, setResumo] = useState<ResumoResponse>({})

  useEffect(() => {
    async function load() {
      try {
        const [resGastos, resResumo] = await Promise.all([
          fetch(apiPath('/api/v1/gastos?page=1&page_size=8')),
          fetch(apiPath('/api/v1/gastos/resumo')),
        ])

        if (!resGastos.ok || !resResumo.ok) {
          throw new Error('api unavailable')
        }

        const gastosJson = (await resGastos.json()) as GastoApiResponse
        const resumoJson = (await resResumo.json()) as ResumoResponse
        const safeItems = Array.isArray(gastosJson.items) ? gastosJson.items : []

        setGastos(safeItems.length > 0 ? safeItems : FALLBACK_GASTOS)
        setResumo(resumoJson)
        setStatus('ready')
      } catch (_error) {
        const total = FALLBACK_GASTOS.reduce((sum, row) => sum + Number(row.valor_empenhado || 0), 0)
        setGastos(FALLBACK_GASTOS)
        setResumo({
          total_empenhado: total,
          quantidade_registros: FALLBACK_GASTOS.length,
          ticket_medio: total / FALLBACK_GASTOS.length,
        })
        setStatus('fallback')
      }
    }

    load()
  }, [])

  const byCategory = useMemo(() => calcByCategory(gastos), [gastos])
  const maxCategory = byCategory[0]?.total || 1

  const kpis = [
    {
      label: 'Total empenhado',
      value: formatBRL(Number(resumo.total_empenhado || 0)),
      sub: 'Consolidado nacional',
    },
    {
      label: 'Registros',
      value: shortNumber(Number(resumo.quantidade_registros || 0)),
      sub: 'Linhas normalizadas',
    },
    {
      label: 'Ticket medio',
      value: formatBRL(Number(resumo.ticket_medio || 0)),
      sub: 'Media por empenho',
    },
  ]

  return (
    <div className="app-shell">
      <aside className="side-panel">
        <div className="brand-wrap">
          <p className="brand-kicker">Transparencia BR</p>
          <h1>IIIbrasil</h1>
          <p>Monitor de gastos publicos integrado e auditavel.</p>
        </div>
        <nav className="nav-tabs" aria-label="Navegacao principal">
          {TABS.map((item) => (
            <button
              key={item.id}
              className={tab === item.id ? 'tab-btn active' : 'tab-btn'}
              onClick={() => setTab(item.id)}
            >
              {item.label}
            </button>
          ))}
        </nav>
        <div className="status-card">
          <span className={status === 'ready' ? 'status-dot ok' : status === 'loading' ? 'status-dot wait' : 'status-dot warn'} />
          <span>
            {status === 'ready' && 'API conectada'}
            {status === 'loading' && 'Carregando dados'}
            {status === 'fallback' && 'Fallback local ativo'}
          </span>
        </div>
      </aside>

      <main className="content">
        <header className="hero">
          <div>
            <p className="eyebrow">Painel executivo</p>
            <h2>UI/UX moderna para monitoramento de despesas</h2>
            <p>Experiencia focada em clareza, velocidade e leitura de decisao.</p>
          </div>
          <button className="primary-btn" onClick={() => setTab('gastos')}>Explorar gastos</button>
        </header>

        {tab === 'dashboard' && (
          <section className="stack">
            <div className="kpi-grid">
              {kpis.map((kpi) => (
                <article key={kpi.label} className="kpi-card">
                  <p>{kpi.label}</p>
                  <strong>{kpi.value}</strong>
                  <span>{kpi.sub}</span>
                </article>
              ))}
            </div>

            <div className="panel-grid">
              <article className="panel">
                <h3>Ultimos empenhos</h3>
                <div className="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>Data</th>
                        <th>Favorecido</th>
                        <th>Funcao</th>
                        <th>UF</th>
                        <th>Valor</th>
                      </tr>
                    </thead>
                    <tbody>
                      {gastos.map((row, index) => (
                        <tr key={`${row.favorecido_nome}-${index}`}>
                          <td>{formatDate(row.data_empenho)}</td>
                          <td>{row.favorecido_nome || '-'}</td>
                          <td>{row.funcao_governo || '-'}</td>
                          <td>{row.uf || '-'}</td>
                          <td>{formatBRL(Number(row.valor_empenhado || 0))}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </article>

              <article className="panel">
                <h3>Distribuicao por funcao</h3>
                <div className="bar-list">
                  {byCategory.slice(0, 6).map((item) => (
                    <div key={item.name} className="bar-item">
                      <div className="bar-meta">
                        <span>{item.name}</span>
                        <strong>{formatBRL(item.total)}</strong>
                      </div>
                      <div className="bar-track">
                        <div className="bar-fill" style={{ width: `${Math.max(6, (item.total / maxCategory) * 100)}%` }} />
                      </div>
                    </div>
                  ))}
                </div>
              </article>
            </div>
          </section>
        )}

        {tab === 'gastos' && (
          <section className="panel single">
            <h3>Tabela de gastos</h3>
            <p className="muted">Visao simplificada para operacao diaria e auditoria rapida.</p>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Data</th>
                    <th>Favorecido</th>
                    <th>Funcao</th>
                    <th>UF</th>
                    <th>Valor</th>
                  </tr>
                </thead>
                <tbody>
                  {gastos.map((row, index) => (
                    <tr key={`g-${index}`}>
                      <td>{formatDate(row.data_empenho)}</td>
                      <td>{row.favorecido_nome || '-'}</td>
                      <td>{row.funcao_governo || '-'}</td>
                      <td>{row.uf || '-'}</td>
                      <td>{formatBRL(Number(row.valor_empenhado || 0))}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        )}

        {tab === 'insights' && (
          <section className="insights-grid">
            <article className="panel">
              <h3>Highlights</h3>
              <ul className="clean-list">
                <li>Layout responsivo com foco em leitura em tela grande e mobile.</li>
                <li>Camada visual com contraste alto e hierarquia clara.</li>
                <li>Indicadores centrais acima da dobra para decisao rapida.</li>
              </ul>
            </article>
            <article className="panel">
              <h3>UX aplicada</h3>
              <ul className="clean-list">
                <li>Navegacao curta em 4 abas, sem sobrecarga cognitiva.</li>
                <li>Tabelas com destaque por hover e alinhamento financeiro.</li>
                <li>Fallback para dados locais quando API estiver indisponivel.</li>
              </ul>
            </article>
          </section>
        )}

        {tab === 'sobre' && (
          <section className="panel single">
            <h3>Sobre esta interface</h3>
            <p>
              Esta versao foi desenhada para ser objetiva, moderna e pronta para evolucao em producao.
              O frontend conversa com <code>/api/v1</code> e mantem experiencia funcional mesmo sem API.
            </p>
          </section>
        )}
      </main>
    </div>
  )
}

export default App
