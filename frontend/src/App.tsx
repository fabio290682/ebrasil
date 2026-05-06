import { useEffect, useMemo, useState } from 'react'
import './App.css'
import { GastosPage } from './pages/GastosPage'

type TabId = 'dashboard' | 'gastos' | 'insights' | 'rpa' | 'ai' | 'sobre'

type GastoItem = {
  id?: number
  data_empenho?: string
  favorecido_nome?: string
  funcao_governo?: string
  valor_empenhado?: number
  uf?: string
}

type MlAnomalia = {
  id: string
  data_empenho: string
  favorecido_nome: string
  valor_empenhado: number
  uf: string
  funcao_governo: string
  anomaly_score: number
  is_anomaly: boolean
}

type MlPrevisaoItem = {
  mes: string
  total: number
  tipo: 'historico' | 'previsao'
}

type MlFornecedorRisco = {
  fornecedor: string
  cnpj_cpf: string
  total_transacoes: number
  total_valor: number
  risk_score: number
  anomalias_detectadas: number
  estados_atuacao: string[]
}

type MlStatus = {
  backend: string
  model_trained: boolean
  trained_at: string | null
  training_size: number
}

type RpaFonte = {
  id: string
  nome: string
  descricao: string
  tipo: 'api' | 'scraper'
  url_base: string
  ativa: boolean
  intervalo_horas: number
  ultima_execucao: string | null
  proxima_execucao: string | null
  em_execucao: boolean
}

type RpaLog = {
  id: string
  fonte_id: string
  status: 'running' | 'success' | 'error' | 'partial' | 'pending'
  registros_buscados: number
  registros_salvos: number
  registros_duplicados: number
  iniciado_em: string
  finalizado_em: string | null
  mensagem: string | null
  duracao_segundos: number | null
}

type RpaStatus = {
  scheduler_ativo: boolean
  em_execucao: string[]
  agentes_registrados: string[]
}

type AiStatus = {
  configurado: boolean
  modelo: string
  prompt_caching: boolean
  funcionalidades: string[]
}

type AiClassificado = {
  data_empenho?: string
  favorecido_nome?: string
  valor_empenhado?: number
  uf?: string
  ai_classificacao: string
  ai_motivo: string
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
  { id: 'insights', label: 'Insights ML' },
  { id: 'rpa', label: 'RPA' },
  { id: 'ai', label: 'IA Claude' },
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

  // ML state
  const [mlAnomalias, setMlAnomalias] = useState<MlAnomalia[]>([])
  const [mlPrevisao, setMlPrevisao] = useState<MlPrevisaoItem[]>([])
  const [mlRisco, setMlRisco] = useState<MlFornecedorRisco[]>([])
  const [mlStatus, setMlStatus] = useState<MlStatus | null>(null)
  const [mlLoading, setMlLoading] = useState(false)
  const [mlFetchMsg, setMlFetchMsg] = useState<string | null>(null)
  const [mlFetchLoading, setMlFetchLoading] = useState(false)

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

  useEffect(() => {
    if (tab !== 'insights') return
    if (mlAnomalias.length > 0 || mlStatus !== null) return  // already loaded

    async function loadMl() {
      setMlLoading(true)
      try {
        const [resStatus, resAnomalias, resPrevisao, resRisco] = await Promise.all([
          fetch(apiPath('/api/v1/ml/status')),
          fetch(apiPath('/api/v1/ml/anomalias?limit=10')),
          fetch(apiPath('/api/v1/ml/previsao?periodos=3')),
          fetch(apiPath('/api/v1/ml/risco-fornecedores?limit=10')),
        ])
        if (resStatus.ok) {
          const s = await resStatus.json() as { detector: MlStatus }
          setMlStatus(s.detector)
        }
        if (resAnomalias.ok) {
          const a = await resAnomalias.json() as { anomalias: MlAnomalia[] }
          setMlAnomalias(a.anomalias ?? [])
        }
        if (resPrevisao.ok) {
          const p = await resPrevisao.json() as { historico: MlPrevisaoItem[]; previsao: MlPrevisaoItem[] }
          setMlPrevisao([...(p.historico ?? []).slice(-6), ...(p.previsao ?? [])])
        }
        if (resRisco.ok) {
          const r = await resRisco.json() as { fornecedores: MlFornecedorRisco[] }
          setMlRisco(r.fornecedores ?? [])
        }
      } catch (_e) {
        // API unavailable — leave empty arrays, UI shows empty state
      } finally {
        setMlLoading(false)
      }
    }
    loadMl()
  }, [tab])

  // RPA state
  const [rpaFontes, setRpaFontes] = useState<RpaFonte[]>([])
  const [rpaLogs, setRpaLogs] = useState<RpaLog[]>([])
  const [rpaStatus, setRpaStatus] = useState<RpaStatus | null>(null)
  const [rpaLoading, setRpaLoading] = useState(false)
  const [rpaRunning, setRpaRunning] = useState<string | null>(null)
  const [rpaMsg, setRpaMsg] = useState<string | null>(null)

  useEffect(() => {
    if (tab !== 'rpa') return
    loadRpa()
  }, [tab])

  async function loadRpa() {
    setRpaLoading(true)
    try {
      const [resFontes, resLogs, resStatus] = await Promise.all([
        fetch(apiPath('/api/v1/rpa/fontes')),
        fetch(apiPath('/api/v1/rpa/logs?limit=20')),
        fetch(apiPath('/api/v1/rpa/status')),
      ])
      if (resFontes.ok) {
        const j = await resFontes.json() as { fontes: RpaFonte[] }
        setRpaFontes(j.fontes ?? [])
      }
      if (resLogs.ok) {
        const j = await resLogs.json() as { logs: RpaLog[] }
        setRpaLogs(j.logs ?? [])
      }
      if (resStatus.ok) {
        setRpaStatus(await resStatus.json() as RpaStatus)
      }
    } catch (_e) {
      // silent
    } finally {
      setRpaLoading(false)
    }
  }

  async function handleRpaRun(fonteId: string) {
    setRpaRunning(fonteId)
    setRpaMsg(null)
    try {
      const res = await fetch(apiPath(`/api/v1/rpa/fontes/${fonteId}/executar`), { method: 'POST' })
      const j = await res.json() as { mensagem?: string }
      setRpaMsg(j.mensagem ?? 'Execucao iniciada em background.')
      setTimeout(loadRpa, 3000)
    } catch (_e) {
      setRpaMsg('Falha ao iniciar execucao.')
    } finally {
      setRpaRunning(null)
    }
  }

  async function handleRpaToggle(fonteId: string, ativa: boolean) {
    try {
      await fetch(apiPath(`/api/v1/rpa/fontes/${fonteId}`), {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ativa }),
      })
      setRpaFontes(prev => prev.map(f => f.id === fonteId ? { ...f, ativa } : f))
    } catch (_e) {
      setRpaMsg('Falha ao alterar status da fonte.')
    }
  }

  async function handleFetchDados() {
    setMlFetchLoading(true)
    setMlFetchMsg(null)
    try {
      const res = await fetch(apiPath('/api/v1/ml/buscar-dados?fonte=camara&deputados_limit=5'), { method: 'POST' })
      const json = await res.json() as { registros_salvos: number; registros_buscados: number }
      setMlFetchMsg(`Buscados ${json.registros_buscados} registros — ${json.registros_salvos} novos salvos.`)
      // Reload ML data after fetch
      setMlAnomalias([])
      setMlStatus(null)
    } catch (_e) {
      setMlFetchMsg('Falha ao buscar dados da fonte. Verifique a conexao com a API.')
    } finally {
      setMlFetchLoading(false)
    }
  }

  // AI state
  const [aiStatus, setAiStatus] = useState<AiStatus | null>(null)
  const [aiRelatorio, setAiRelatorio] = useState<string | null>(null)
  const [aiAnalise, setAiAnalise] = useState<string | null>(null)
  const [aiClassificados, setAiClassificados] = useState<AiClassificado[]>([])
  const [aiLoading, setAiLoading] = useState<string | null>(null)

  useEffect(() => {
    if (tab !== 'ai') return
    if (aiStatus !== null) return
    fetch(apiPath('/api/v1/ai/status'))
      .then(r => r.ok ? r.json() as Promise<AiStatus> : null)
      .then(s => { if (s) setAiStatus(s) })
      .catch(() => undefined)
  }, [tab])

  async function handleAiRelatorio() {
    setAiLoading('relatorio')
    setAiRelatorio(null)
    try {
      const res = await fetch(apiPath('/api/v1/ai/relatorio-diario'))
      if (res.ok) {
        const j = await res.json() as { relatorio: string }
        setAiRelatorio(j.relatorio)
      }
    } catch (_e) {
      setAiRelatorio('Falha ao gerar relatorio. Verifique a chave ANTHROPIC_API_KEY.')
    } finally {
      setAiLoading(null)
    }
  }

  async function handleAiAnomalia() {
    setAiLoading('anomalia')
    setAiAnalise(null)
    try {
      const res = await fetch(apiPath('/api/v1/ml/anomalias?limit=30'))
      const j = res.ok ? await res.json() as { anomalias: MlAnomalia[] } : { anomalias: [] }
      const anomalias = j.anomalias.filter(a => a.is_anomaly)
      if (anomalias.length === 0) {
        setAiAnalise('Nenhuma anomalia detectada nos dados atuais para analisar.')
        return
      }
      const res2 = await fetch(apiPath('/api/v1/ai/analisar-anomalias'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ registros: anomalias }),
      })
      if (res2.ok) {
        const j2 = await res2.json() as { analise: string }
        setAiAnalise(j2.analise)
      }
    } catch (_e) {
      setAiAnalise('Falha na analise de anomalias.')
    } finally {
      setAiLoading(null)
    }
  }

  async function handleAiClassificar() {
    setAiLoading('classificar')
    setAiClassificados([])
    try {
      const res = await fetch(apiPath('/api/v1/gastos?page=1&page_size=20'))
      const j = res.ok ? await res.json() as { items: GastoItem[] } : { items: [] }
      const items = j.items ?? []
      if (items.length === 0) {
        setAiClassificados([])
        return
      }
      const res2 = await fetch(apiPath('/api/v1/ai/classificar-lote'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ registros: items }),
      })
      if (res2.ok) {
        const j2 = await res2.json() as { registros: AiClassificado[] }
        setAiClassificados(j2.registros ?? [])
      }
    } catch (_e) {
      setAiClassificados([])
    } finally {
      setAiLoading(null)
    }
  }

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
          <section className="panel single" style={{ padding: 0, background: 'transparent', border: 'none', boxShadow: 'none' }}>
            <GastosPage />
          </section>
        )}

        {tab === 'insights' && (
          <section className="stack">
            {/* Header + Data Fetch */}
            <div className="panel" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem' }}>
              <div>
                <h3 style={{ margin: 0 }}>Insights por Machine Learning</h3>
                <p className="muted" style={{ margin: '0.25rem 0 0' }}>
                  Anomalias detectadas por Isolation Forest · Previsao por media movel · Score de risco de fornecedores
                  {mlStatus && (
                    <span style={{ marginLeft: '0.75rem', opacity: 0.7 }}>
                      — modelo: {mlStatus.backend} · {mlStatus.model_trained ? `treinado com ${mlStatus.training_size} registros` : 'nao treinado'}
                    </span>
                  )}
                </p>
              </div>
              <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                {mlFetchMsg && <span className="muted" style={{ fontSize: '0.8rem' }}>{mlFetchMsg}</span>}
                <button
                  className="primary-btn"
                  onClick={handleFetchDados}
                  disabled={mlFetchLoading}
                  style={{ whiteSpace: 'nowrap' }}
                >
                  {mlFetchLoading ? 'Buscando...' : 'Buscar dados da fonte'}
                </button>
              </div>
            </div>

            {mlLoading && (
              <div className="panel" style={{ textAlign: 'center', padding: '2rem' }}>
                <p className="muted">Carregando analise ML...</p>
              </div>
            )}

            {!mlLoading && (
              <div className="panel-grid">
                {/* Anomaly Alerts */}
                <article className="panel" style={{ gridColumn: 'span 2' }}>
                  <h3>Alertas de anomalia de gasto</h3>
                  {mlAnomalias.length === 0 ? (
                    <p className="muted">Nenhuma anomalia detectada com os dados atuais.</p>
                  ) : (
                    <div className="table-wrap">
                      <table>
                        <thead>
                          <tr>
                            <th>Data</th>
                            <th>Favorecido</th>
                            <th>UF</th>
                            <th>Funcao</th>
                            <th>Valor</th>
                            <th>Score</th>
                          </tr>
                        </thead>
                        <tbody>
                          {mlAnomalias.map((row) => (
                            <tr key={row.id} style={{ background: row.anomaly_score > 0.8 ? 'rgba(220,38,38,0.08)' : undefined }}>
                              <td>{formatDate(row.data_empenho)}</td>
                              <td>{row.favorecido_nome}</td>
                              <td>{row.uf}</td>
                              <td>{row.funcao_governo || '-'}</td>
                              <td>{formatBRL(row.valor_empenhado)}</td>
                              <td>
                                <span style={{
                                  display: 'inline-block',
                                  padding: '0.1rem 0.4rem',
                                  borderRadius: '0.25rem',
                                  fontSize: '0.75rem',
                                  fontWeight: 600,
                                  background: row.anomaly_score > 0.8 ? '#fee2e2' : '#fef9c3',
                                  color: row.anomaly_score > 0.8 ? '#991b1b' : '#713f12',
                                }}>
                                  {(row.anomaly_score * 100).toFixed(0)}%
                                </span>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </article>

                {/* Forecast chart */}
                <article className="panel">
                  <h3>Previsao de gastos (proximos 3 meses)</h3>
                  {mlPrevisao.length === 0 ? (
                    <p className="muted">Dados insuficientes para previsao.</p>
                  ) : (
                    <div className="bar-list">
                      {mlPrevisao.map((item) => {
                        const maxVal = Math.max(...mlPrevisao.map((i) => i.total), 1)
                        return (
                          <div key={item.mes} className="bar-item">
                            <div className="bar-meta">
                              <span style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                                {item.mes}
                                {item.tipo === 'previsao' && (
                                  <span style={{ fontSize: '0.7rem', padding: '0 0.3rem', borderRadius: '0.2rem', background: '#dbeafe', color: '#1e40af' }}>prev</span>
                                )}
                              </span>
                              <strong>{formatBRL(item.total)}</strong>
                            </div>
                            <div className="bar-track">
                              <div
                                className="bar-fill"
                                style={{
                                  width: `${Math.max(4, (item.total / maxVal) * 100)}%`,
                                  opacity: item.tipo === 'previsao' ? 0.55 : 1,
                                  background: item.tipo === 'previsao' ? '#60a5fa' : undefined,
                                }}
                              />
                            </div>
                          </div>
                        )
                      })}
                    </div>
                  )}
                </article>

                {/* Supplier risk */}
                <article className="panel">
                  <h3>Ranking de risco de fornecedores</h3>
                  {mlRisco.length === 0 ? (
                    <p className="muted">Nenhum dado de risco disponivel.</p>
                  ) : (
                    <div className="bar-list">
                      {mlRisco.map((s) => (
                        <div key={s.fornecedor} className="bar-item">
                          <div className="bar-meta">
                            <span title={s.cnpj_cpf || undefined}>{s.fornecedor.length > 28 ? `${s.fornecedor.slice(0, 28)}…` : s.fornecedor}</span>
                            <strong style={{ color: s.risk_score > 70 ? '#dc2626' : s.risk_score > 40 ? '#d97706' : undefined }}>
                              {s.risk_score.toFixed(0)}/100
                            </strong>
                          </div>
                          <div className="bar-track">
                            <div
                              className="bar-fill"
                              style={{
                                width: `${Math.max(4, s.risk_score)}%`,
                                background: s.risk_score > 70 ? '#ef4444' : s.risk_score > 40 ? '#f59e0b' : '#22c55e',
                              }}
                            />
                          </div>
                          <div style={{ fontSize: '0.72rem', opacity: 0.65, marginTop: '0.1rem' }}>
                            {s.total_transacoes} transacoes · {s.anomalias_detectadas} anomalias · {s.estados_atuacao.join(', ')}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </article>
              </div>
            )}
          </section>
        )}

        {tab === 'rpa' && (
          <section className="stack">
            {/* Header */}
            <div className="panel" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem' }}>
              <div>
                <h3 style={{ margin: 0 }}>RPA — Busca Automatizada em Dados Publicos</h3>
                <p className="muted" style={{ margin: '0.25rem 0 0' }}>
                  Conexao direta (API) e indireta (scraper) com fontes governamentais.
                  {rpaStatus && (
                    <span style={{ marginLeft: '0.5rem' }}>
                      Scheduler: <strong style={{ color: rpaStatus.scheduler_ativo ? '#16a34a' : '#dc2626' }}>
                        {rpaStatus.scheduler_ativo ? 'ativo' : 'parado'}
                      </strong>
                      {rpaStatus.em_execucao.length > 0 && (
                        <span style={{ marginLeft: '0.5rem', color: '#d97706' }}>
                          Em execucao: {rpaStatus.em_execucao.join(', ')}
                        </span>
                      )}
                    </span>
                  )}
                </p>
                {rpaMsg && <p style={{ margin: '0.25rem 0 0', fontSize: '0.8rem', color: '#2563eb' }}>{rpaMsg}</p>}
              </div>
              <button className="primary-btn" onClick={loadRpa} disabled={rpaLoading}>
                {rpaLoading ? 'Atualizando...' : 'Atualizar'}
              </button>
            </div>

            {rpaLoading && (
              <div className="panel" style={{ textAlign: 'center', padding: '2rem' }}>
                <p className="muted">Carregando status do RPA...</p>
              </div>
            )}

            {!rpaLoading && (
              <div className="panel-grid">
                {/* Fontes de dados */}
                <article className="panel" style={{ gridColumn: 'span 2' }}>
                  <h3>Fontes de dados</h3>
                  {rpaFontes.length === 0 ? (
                    <p className="muted">Nenhuma fonte cadastrada. Reinicie o backend para inicializar.</p>
                  ) : (
                    <div className="table-wrap">
                      <table>
                        <thead>
                          <tr>
                            <th>Fonte</th>
                            <th>Tipo</th>
                            <th>Intervalo</th>
                            <th>Ultima execucao</th>
                            <th>Proxima</th>
                            <th>Status</th>
                            <th>Acao</th>
                          </tr>
                        </thead>
                        <tbody>
                          {rpaFontes.map((f) => (
                            <tr key={f.id}>
                              <td>
                                <strong>{f.nome}</strong>
                                <div style={{ fontSize: '0.72rem', opacity: 0.6 }}>{f.descricao?.slice(0, 55)}{(f.descricao?.length ?? 0) > 55 ? '…' : ''}</div>
                              </td>
                              <td>
                                <span style={{
                                  padding: '0.1rem 0.4rem',
                                  borderRadius: '0.25rem',
                                  fontSize: '0.72rem',
                                  fontWeight: 600,
                                  background: f.tipo === 'api' ? '#dbeafe' : '#fef3c7',
                                  color: f.tipo === 'api' ? '#1e40af' : '#92400e',
                                }}>
                                  {f.tipo === 'api' ? 'API direta' : 'Scraper'}
                                </span>
                              </td>
                              <td>{f.intervalo_horas}h</td>
                              <td style={{ fontSize: '0.8rem' }}>
                                {f.ultima_execucao ? formatDate(f.ultima_execucao.slice(0, 10)) : '—'}
                              </td>
                              <td style={{ fontSize: '0.8rem' }}>
                                {f.proxima_execucao ? formatDate(f.proxima_execucao.slice(0, 10)) : 'Agendada'}
                              </td>
                              <td>
                                <button
                                  onClick={() => handleRpaToggle(f.id, !f.ativa)}
                                  style={{
                                    background: 'none',
                                    border: 'none',
                                    cursor: 'pointer',
                                    fontWeight: 600,
                                    color: f.ativa ? '#16a34a' : '#6b7280',
                                    fontSize: '0.8rem',
                                  }}
                                >
                                  {f.em_execucao ? '⟳ rodando' : f.ativa ? '● ativa' : '○ pausada'}
                                </button>
                              </td>
                              <td>
                                <button
                                  className="primary-btn"
                                  onClick={() => handleRpaRun(f.id)}
                                  disabled={rpaRunning === f.id || f.em_execucao || !f.ativa}
                                  style={{ padding: '0.25rem 0.6rem', fontSize: '0.78rem' }}
                                >
                                  {rpaRunning === f.id ? 'Iniciando...' : 'Executar'}
                                </button>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </article>

                {/* Historico de execucoes */}
                <article className="panel" style={{ gridColumn: 'span 2' }}>
                  <h3>Historico de execucoes</h3>
                  {rpaLogs.length === 0 ? (
                    <p className="muted">Nenhuma execucao registrada ainda. Clique em "Executar" em uma fonte.</p>
                  ) : (
                    <div className="table-wrap">
                      <table>
                        <thead>
                          <tr>
                            <th>Fonte</th>
                            <th>Status</th>
                            <th>Buscados</th>
                            <th>Salvos</th>
                            <th>Duplicados</th>
                            <th>Duracao</th>
                            <th>Inicio</th>
                            <th>Mensagem</th>
                          </tr>
                        </thead>
                        <tbody>
                          {rpaLogs.map((log) => {
                            const statusColors: Record<string, { bg: string; fg: string }> = {
                              success: { bg: '#dcfce7', fg: '#15803d' },
                              error: { bg: '#fee2e2', fg: '#dc2626' },
                              running: { bg: '#dbeafe', fg: '#1d4ed8' },
                              partial: { bg: '#fef9c3', fg: '#854d0e' },
                              pending: { bg: '#f3f4f6', fg: '#374151' },
                            }
                            const c = statusColors[log.status] ?? statusColors.pending
                            return (
                              <tr key={log.id}>
                                <td><strong>{log.fonte_id}</strong></td>
                                <td>
                                  <span style={{ padding: '0.1rem 0.4rem', borderRadius: '0.25rem', fontSize: '0.72rem', fontWeight: 600, background: c.bg, color: c.fg }}>
                                    {log.status}
                                  </span>
                                </td>
                                <td>{log.registros_buscados}</td>
                                <td>{log.registros_salvos}</td>
                                <td>{log.registros_duplicados}</td>
                                <td>{log.duracao_segundos != null ? `${log.duracao_segundos}s` : '—'}</td>
                                <td style={{ fontSize: '0.78rem' }}>{formatDate(log.iniciado_em?.slice(0, 10))}</td>
                                <td style={{ fontSize: '0.72rem', maxWidth: '160px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={log.mensagem ?? undefined}>
                                  {log.mensagem ?? '—'}
                                </td>
                              </tr>
                            )
                          })}
                        </tbody>
                      </table>
                    </div>
                  )}
                </article>

                {/* Legenda de conexoes */}
                <article className="panel">
                  <h3>Tipos de conexao</h3>
                  <div className="bar-list">
                    {[
                      { label: 'API direta', desc: 'Camara, Senado, Portal da Transparencia, PNCP, Brasil API', color: '#dbeafe', fg: '#1e40af' },
                      { label: 'Scraper indireto', desc: 'Betha (portais municipais), TCEs estaduais via HTTP', color: '#fef3c7', fg: '#92400e' },
                    ].map((item) => (
                      <div key={item.label} className="bar-item" style={{ borderLeft: `3px solid ${item.fg}`, paddingLeft: '0.75rem' }}>
                        <div className="bar-meta">
                          <strong style={{ color: item.fg }}>{item.label}</strong>
                        </div>
                        <div style={{ fontSize: '0.8rem', opacity: 0.75, marginTop: '0.2rem' }}>{item.desc}</div>
                      </div>
                    ))}
                  </div>
                </article>

                {/* Agentes registrados */}
                <article className="panel">
                  <h3>Agentes registrados</h3>
                  {rpaStatus ? (
                    <div className="bar-list">
                      {rpaStatus.agentes_registrados.map((a) => {
                        const fonte = rpaFontes.find(f => f.id === a)
                        return (
                          <div key={a} className="bar-item">
                            <div className="bar-meta">
                              <span>{fonte?.nome ?? a}</span>
                              <strong style={{ fontSize: '0.75rem', opacity: 0.6 }}>{fonte?.tipo ?? ''}</strong>
                            </div>
                          </div>
                        )
                      })}
                    </div>
                  ) : (
                    <p className="muted">API indisponivel.</p>
                  )}
                </article>
              </div>
            )}
          </section>
        )}

        {tab === 'ai' && (
          <section className="stack">
            <div className="panel single" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.75rem' }}>
              <div>
                <h3 style={{ marginBottom: '0.25rem' }}>IA Claude — Analise de Gastos</h3>
                <p className="muted" style={{ margin: 0 }}>
                  {aiStatus
                    ? aiStatus.configurado
                      ? `Modelo: ${aiStatus.modelo} | Prompt caching ativo`
                      : 'ANTHROPIC_API_KEY nao configurada — configure no painel Render.'
                    : 'Verificando configuracao...'}
                </p>
              </div>
              {aiStatus && (
                <span style={{
                  padding: '0.25rem 0.6rem', borderRadius: '0.4rem', fontSize: '0.75rem', fontWeight: 600,
                  background: aiStatus.configurado ? '#dcfce7' : '#fee2e2',
                  color: aiStatus.configurado ? '#15803d' : '#dc2626',
                }}>
                  {aiStatus.configurado ? 'Conectado' : 'Sem chave'}
                </span>
              )}
            </div>

            <div className="panel-grid">
              {/* Relatorio diario */}
              <article className="panel">
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
                  <h3 style={{ margin: 0 }}>Relatorio diario</h3>
                  <button className="primary-btn" onClick={handleAiRelatorio} disabled={aiLoading === 'relatorio'}>
                    {aiLoading === 'relatorio' ? 'Gerando...' : 'Gerar relatorio'}
                  </button>
                </div>
                {aiRelatorio ? (
                  <div style={{ whiteSpace: 'pre-wrap', fontSize: '0.85rem', lineHeight: 1.6, background: '#f8fafc', borderRadius: '0.5rem', padding: '1rem' }}>
                    {aiRelatorio}
                  </div>
                ) : (
                  <p className="muted">Clique em "Gerar relatorio" para obter uma analise dos ultimos 7 dias elaborada pela IA.</p>
                )}
              </article>

              {/* Analise de anomalias */}
              <article className="panel">
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
                  <h3 style={{ margin: 0 }}>Analise de anomalias</h3>
                  <button className="primary-btn" onClick={handleAiAnomalia} disabled={aiLoading === 'anomalia'}>
                    {aiLoading === 'anomalia' ? 'Analisando...' : 'Analisar anomalias'}
                  </button>
                </div>
                {aiAnalise ? (
                  <div style={{ whiteSpace: 'pre-wrap', fontSize: '0.85rem', lineHeight: 1.6, background: '#f8fafc', borderRadius: '0.5rem', padding: '1rem' }}>
                    {aiAnalise}
                  </div>
                ) : (
                  <p className="muted">Busca anomalias detectadas pelo ML e solicita interpretacao da IA.</p>
                )}
              </article>

              {/* Classificacao de risco */}
              <article className="panel">
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
                  <h3 style={{ margin: 0 }}>Classificacao de risco (lote)</h3>
                  <button className="primary-btn" onClick={handleAiClassificar} disabled={aiLoading === 'classificar'}>
                    {aiLoading === 'classificar' ? 'Classificando...' : 'Classificar ultimos gastos'}
                  </button>
                </div>
                {aiClassificados.length > 0 ? (
                  <div className="table-wrap">
                    <table>
                      <thead>
                        <tr>
                          <th>Favorecido</th>
                          <th>Valor</th>
                          <th>UF</th>
                          <th>Risco IA</th>
                          <th>Motivo</th>
                        </tr>
                      </thead>
                      <tbody>
                        {aiClassificados.map((row, i) => {
                          const riskColors: Record<string, { bg: string; fg: string }> = {
                            CRITICO: { bg: '#fee2e2', fg: '#dc2626' },
                            ALTO: { bg: '#ffedd5', fg: '#c2410c' },
                            MEDIO: { bg: '#fef9c3', fg: '#854d0e' },
                            BAIXO: { bg: '#dcfce7', fg: '#15803d' },
                            INDEFINIDO: { bg: '#f3f4f6', fg: '#374151' },
                          }
                          const c = riskColors[row.ai_classificacao] ?? riskColors.INDEFINIDO
                          return (
                            <tr key={i}>
                              <td style={{ maxWidth: 160, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                {row.favorecido_nome ?? '—'}
                              </td>
                              <td>{row.valor_empenhado != null ? formatBRL(row.valor_empenhado) : '—'}</td>
                              <td>{row.uf ?? '—'}</td>
                              <td>
                                <span style={{ padding: '0.1rem 0.4rem', borderRadius: '0.25rem', fontSize: '0.72rem', fontWeight: 600, background: c.bg, color: c.fg }}>
                                  {row.ai_classificacao}
                                </span>
                              </td>
                              <td style={{ fontSize: '0.75rem', maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={row.ai_motivo}>
                                {row.ai_motivo || '—'}
                              </td>
                            </tr>
                          )
                        })}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <p className="muted">Classifica os 20 gastos mais recentes com BAIXO / MEDIO / ALTO / CRITICO.</p>
                )}
              </article>
            </div>
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
