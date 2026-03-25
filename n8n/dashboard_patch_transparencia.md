# Patch sugerido para `dashboard_transparencia.html`

Como o arquivo informado está fora do workspace (`c:\Users\Super economico\Downloads\dashboard_transparencia.html`), segue o bloco pronto para aplicar.

## 1) Novo KPI - Cota Parlamentar

Inserir dentro de `<div class="kpi-grid">`:

```html
<div class="kpi-card">
  <div class="kpi-header">
    <span class="kpi-label">Cota Parlamentar (Mes)</span>
    <div class="kpi-icon orange">
      <svg viewBox="0 0 20 20" fill="none" stroke="#C8832A" stroke-width="2">
        <path d="M16 17l-4-4m0-8l4 4m-12 0l4-4m0 8l-4 4" stroke-linecap="round"/>
      </svg>
    </div>
  </div>
  <div class="kpi-value" id="kpi-cota-parlamentar">R$ 0,00</div>
  <div class="kpi-meta">
    <span class="kpi-delta up" id="kpi-cota-delta">-</span> Deputados e Senadores
  </div>
</div>
```

## 2) Filtro por Poder/Categoria

Inserir na seção de busca:

```html
<select class="search-select" id="filtro-poder">
  <option value="">Todos os Poderes</option>
  <option value="Executivo Federal">Executivo (Ministerios)</option>
  <option value="Legislativo Federal">Legislativo (Deputados e Senadores)</option>
  <option value="Judiciario">Judiciario</option>
</select>
```

## 3) Render de gastos com novos campos

Atualizar o mapeamento JS para suportar:

```js
function mapGasto(row) {
  return {
    data: row.data_empenho,
    municipio: row.municipio_nome || 'Brasilia',
    uf: row.uf || 'DF',
    favorecido: row.favorecido_nome || 'Nao informado',
    agente: row.agente_publico || '-',
    elemento: row.tipo_despesa || row.elemento_despesa || '-',
    sistema: row.fornecedor_sistema || '-',
    valor: Number(row.valor_empenhado || 0),
    status: 'ok',
    categoria: row.categoria_origem || '-',
    partido: row.partido || '-'
  };
}
```

Exemplo de uso na chamada da API:

```js
const params = new URLSearchParams({
  page: '1',
  page_size: '50',
});
const poder = document.getElementById('filtro-poder').value;
if (poder) params.set('categoria_origem', poder);

const res = await fetch(`/api/v1/gastos?${params.toString()}`);
const json = await res.json();
const rows = json.items.map(mapGasto);
```

## 4) Novo endpoint de resumo legislativo (opcional no front)

```js
const resLeg = await fetch('/api/v1/gastos/resumo?categoria_origem=Legislativo%20Federal');
const leg = await resLeg.json();
document.getElementById('kpi-cota-parlamentar').textContent =
  leg.total_empenhado.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
```
