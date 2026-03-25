// n8n Code Node - normalizador universal (Schema Unico)
// Entrada esperada por item:
// {
//   fonte: {...metadados da fonte...},
//   payload: {...registro bruto da API...}
// }

function pick(obj, paths, fallback = null) {
  for (const path of paths) {
    const parts = path.split('.');
    let value = obj;
    let ok = true;
    for (const p of parts) {
      if (value && Object.prototype.hasOwnProperty.call(value, p)) {
        value = value[p];
      } else {
        ok = false;
        break;
      }
    }
    if (ok && value !== undefined && value !== null && value !== '') {
      return value;
    }
  }
  return fallback;
}

function onlyDigits(v) {
  return String(v || '').replace(/\D/g, '');
}

function toNumber(value) {
  if (typeof value === 'number') return value;
  if (!value) return 0;
  const normalized = String(value)
    .replace(/R\$\s?/g, '')
    .replace(/\./g, '')
    .replace(',', '.')
    .trim();
  const n = Number(normalized);
  return Number.isFinite(n) ? n : 0;
}

function toISODate(v) {
  if (!v) return null;
  const str = String(v).trim();
  if (/^\d{4}-\d{2}-\d{2}/.test(str)) return str.slice(0, 10);
  const br = str.match(/^(\d{2})\/(\d{2})\/(\d{4})$/);
  if (br) return `${br[3]}-${br[2]}-${br[1]}`;
  return null;
}

function buildId(raw, fonte) {
  const base =
    pick(raw, ['id', 'id_transacao', 'hash']) ||
    `${pick(raw, ['numero_empenho', 'num_empenho', 'numero', 'empenho.numero'], 'sem_numero')}` +
      `:${pick(raw, ['data_empenho', 'dt_emissao', 'data_gasto'], 'sem_data')}` +
      `:${pick(raw, ['valor_empenhado', 'valor_pago', 'total'], '0')}` +
      `:${fonte?.municipio_ibge || '0000000'}`;
  return `${fonte?.id || 'fonte'}:${String(base).slice(0, 180)}`;
}

const out = [];

for (const item of items) {
  const fonte = item.json.fonte || {};
  const raw = item.json.payload || item.json;
  const map = fonte.mapeamento_campos || {};

  const dataEmpenho =
    toISODate(
      pick(raw, [map.data_empenho].filter(Boolean).concat([
        'data_empenho',
        'dataEmpenho',
        'dt_emissao',
        'data_gasto'
      ]))
    );

  const unificado = {
    id_transacao: buildId(raw, fonte),
    fonte_id: fonte.id || null,
    categoria_origem: fonte.categoria_origem || pick(raw, ['categoria_origem'], null),
    agente_publico: pick(raw, [map.agente_publico].filter(Boolean).concat([
      'agente_publico',
      'nomeParlamentar',
      'deputado.nome',
      'senador.nome',
      'ministro'
    ]), null),
    partido: pick(raw, [map.partido].filter(Boolean).concat([
      'partido',
      'siglaPartido',
      'deputado.siglaPartido',
      'senador.siglaPartido'
    ]), null),
    tipo_despesa: pick(raw, [map.tipo_despesa].filter(Boolean).concat([
      'tipo_despesa',
      'tipoDespesa',
      'descricaoTipo',
      'subelemento'
    ]), null),
    data_empenho: dataEmpenho,
    valor_empenhado: toNumber(
      pick(raw, [map.valor_empenhado].filter(Boolean).concat([
        'valor_empenhado',
        'valorEmpenho',
        'valor_pago',
        'total'
      ]), 0)
    ),
    favorecido_nome: pick(raw, [map.favorecido_nome].filter(Boolean).concat([
      'favorecido_nome',
      'fornecedor.nomeRazaoSocial',
      'credor',
      'razao_social'
    ]), 'NAO INFORMADO'),
    favorecido_cnpj_cpf: onlyDigits(
      pick(raw, [map.favorecido_cnpj_cpf].filter(Boolean).concat([
        'favorecido_cnpj_cpf',
        'fornecedor.cpfCnpj',
        'cpf_cnpj'
      ]), '')
    ),
    elemento_despesa: String(
      pick(raw, [map.elemento_despesa].filter(Boolean).concat([
        'elemento_despesa',
        'elementoDespesa.codigo'
      ]), '')
    ).replace(/\./g, ''),
    fonte_recurso: pick(raw, [map.fonte_recurso].filter(Boolean).concat([
      'fonte_recurso',
      'fonteRecurso.codigo'
    ]), null),
    funcao_governo: pick(raw, [map.funcao_governo].filter(Boolean).concat([
      'funcao_governo',
      'funcao.descricao'
    ]), null),
    numero_empenho: String(
      pick(raw, [map.numero_empenho].filter(Boolean).concat([
        'numero_empenho',
        'num_empenho',
        'numero'
      ]), '')
    ),
    municipio_nome: fonte.municipio_nome || pick(raw, ['municipio', 'cidade_nome'], null),
    municipio_ibge: String(fonte.municipio_ibge || pick(raw, ['municipio_ibge'], '')).padStart(7, '0'),
    uf: String(fonte.uf || pick(raw, ['uf'], '')).toUpperCase().slice(0, 2),
    fornecedor_sistema: fonte.sistema_fornecedor || null,
    url_origem: fonte.url_base || null,
    atualizado_em: new Date().toISOString(),
    payload_origem: raw
  };

  out.push({ json: unificado });
}

return out;
