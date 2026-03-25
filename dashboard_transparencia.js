let dados = [
  { data: '2026-03-23', ente: 'Dep. Federal Exemplo', favorecido: 'Posto Combustivel X', valor: 450, status: 'Validado', categoria: 'Legislativo Federal' },
  { data: '2026-03-23', ente: 'Prefeitura de Tiangua', favorecido: 'Construtora Norte', valor: 125400, status: 'Processado', categoria: 'Municipal' },
  { data: '2026-03-22', ente: 'Senador Exemplo', favorecido: 'CIA Aerea Y', valor: 1890.35, status: 'Validado', categoria: 'Legislativo Federal' },
  { data: '2026-03-21', ente: 'Ministerio da Saude', favorecido: 'Fornecedor Z', valor: 287000, status: 'Processado', categoria: 'Executivo Federal' },
]

function brl(valor) {
  return Number(valor || 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
}

function filtrar() {
  const categoria = document.getElementById('filtro-global').value
  if (!categoria) return dados
  return dados.filter((item) => item.categoria === categoria)
}

function statusClass(status) {
  const normalizado = String(status || '').toLowerCase()
  if (normalizado.includes('valid')) return 'status-validado'
  if (normalizado.includes('process')) return 'status-processado'
  return 'status-erro'
}

function renderTabela() {
  const tbody = document.getElementById('rows')
  const rows = filtrar()

  tbody.innerHTML = rows
    .map((row) => {
      const dt = row.data ? new Date(`${row.data}T00:00:00`).toLocaleDateString('pt-BR') : '-'
      return `
        <tr>
          <td>${dt}</td>
          <td>${row.ente || '-'}</td>
          <td>${row.favorecido || '-'}</td>
          <td>${row.categoria || '-'}</td>
          <td>${brl(row.valor)}</td>
          <td><span class="status-pill ${statusClass(row.status)}">${row.status || 'Indefinido'}</span></td>
        </tr>
      `
    })
    .join('')
}

function renderKpis() {
  const rows = filtrar()
  const total = rows.reduce((sum, row) => sum + Number(row.valor || 0), 0)
  const parlamentar = rows
    .filter((row) => row.categoria === 'Legislativo Federal')
    .reduce((sum, row) => sum + Number(row.valor || 0), 0)
  const municipios = new Set(rows.filter((row) => row.categoria === 'Municipal').map((row) => row.ente)).size

  document.getElementById('kpi-total').textContent = brl(total)
  document.getElementById('kpi-parlamentar').textContent = brl(parlamentar)
  document.getElementById('kpi-municipios').textContent = String(municipios || 0)
}

function renderGrafico() {
  const canvas = document.getElementById('chart')
  if (!canvas) return

  const ctx = canvas.getContext('2d')
  if (!ctx) return

  const rows = filtrar()
  const grupos = rows.reduce((acc, row) => {
    const key = row.categoria || 'Outros'
    acc[key] = (acc[key] || 0) + Number(row.valor || 0)
    return acc
  }, {})

  const labels = Object.keys(grupos)
  const valores = Object.values(grupos)
  const total = valores.reduce((sum, value) => sum + Number(value || 0), 0) || 1
  const cores = ['#32d6b2', '#4ba3ff', '#fcbf49', '#ff8f8f', '#9f7aea']

  ctx.clearRect(0, 0, canvas.width, canvas.height)

  const cx = 108
  const cy = 118
  const raio = 84
  let inicio = -Math.PI / 2

  valores.forEach((valor, idx) => {
    const angulo = (Number(valor) / total) * Math.PI * 2
    ctx.beginPath()
    ctx.moveTo(cx, cy)
    ctx.arc(cx, cy, raio, inicio, inicio + angulo)
    ctx.closePath()
    ctx.fillStyle = cores[idx % cores.length]
    ctx.fill()
    inicio += angulo
  })

  ctx.beginPath()
  ctx.arc(cx, cy, 45, 0, Math.PI * 2)
  ctx.fillStyle = '#103343'
  ctx.fill()

  ctx.fillStyle = '#e9f5fb'
  ctx.font = '700 11px Manrope'
  ctx.textAlign = 'center'
  ctx.fillText('Total', cx, cy - 3)
  ctx.font = '800 14px Manrope'
  ctx.fillText(brl(total), cx, cy + 16)

  ctx.textAlign = 'left'
  labels.forEach((label, idx) => {
    const y = 38 + idx * 24
    ctx.fillStyle = cores[idx % cores.length]
    ctx.fillRect(225, y, 12, 12)
    ctx.fillStyle = '#e9f5fb'
    ctx.font = '600 12px Manrope'
    ctx.fillText(label, 244, y + 10)
  })
}

function exportarCsv() {
  const rows = filtrar()
  const header = ['data', 'ente', 'favorecido', 'categoria', 'valor', 'status']
  const csv = [
    header.join(','),
    ...rows.map((row) =>
      [row.data, row.ente, row.favorecido, row.categoria, row.valor, row.status]
        .map((value) => `"${String(value ?? '').replace(/"/g, '""')}"`)
        .join(','),
    ),
  ].join('\n')

  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = 'transparencia_filtrado.csv'
  link.click()
  URL.revokeObjectURL(link.href)
}

async function carregarDadosApi() {
  try {
    const response = await fetch('http://127.0.0.1:8000/api/v1/integracoes/portal/despesas?pagina=1')
    if (!response.ok) throw new Error(`HTTP ${response.status}`)

    const json = await response.json()
    if (Array.isArray(json.items) && json.items.length > 0) {
      dados = json.items
    }
  } catch (_error) {
    // fallback para dados locais
  }
}

function atualizarTudo() {
  renderTabela()
  renderKpis()
  renderGrafico()
}

document.getElementById('filtro-global').addEventListener('change', atualizarTudo)
document.getElementById('export-csv').addEventListener('click', exportarCsv)

const menu = document.getElementById('menu-toggle')
const sidebar = document.getElementById('sidebar')
menu.addEventListener('click', () => {
  const aberto = sidebar.classList.toggle('open')
  menu.setAttribute('aria-expanded', aberto ? 'true' : 'false')
})

document.querySelectorAll('.menu-btn').forEach((btn) => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.menu-btn').forEach((item) => item.classList.remove('active'))
    btn.classList.add('active')

    if (window.innerWidth <= 860) {
      sidebar.classList.remove('open')
      menu.setAttribute('aria-expanded', 'false')
    }
  })
})

;(async () => {
  await carregarDadosApi()
  atualizarTudo()
})()
