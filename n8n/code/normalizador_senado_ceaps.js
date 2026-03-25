// n8n Code Node - Normalizador CEAPS (Senado Federal)
// Entrada: itens da API do Senado em item.json (registro individual)

function toISODate(v) {
  if (!v) return null;
  const s = String(v).trim();
  if (/^\d{4}-\d{2}-\d{2}/.test(s)) return s.slice(0, 10);
  const br = s.match(/^(\d{2})\/(\d{2})\/(\d{4})$/);
  if (br) return `${br[3]}-${br[2]}-${br[1]}`;
  return null;
}

function toNumber(v) {
  if (typeof v === 'number') return v;
  if (!v) return 0;
  const n = Number(String(v).replace(/\./g, '').replace(',', '.'));
  return Number.isFinite(n) ? n : 0;
}

const out = [];
for (const item of items) {
  const raw = item.json;
  const idBase = raw.idDespesa || raw.documento || raw.hash || `${raw.data || 'sem_data'}:${raw.valor || 0}`;
  out.push({
    json: {
      id_transacao: `senado:${idBase}`,
      fonte_id: raw.fonte_id || null,
      categoria_origem: 'Legislativo Federal',
      agente_publico: raw.nomeSenador || raw.senador || null,
      partido: raw.siglaPartido || raw.partido || null,
      tipo_despesa: raw.tipoDespesa || raw.descricao || 'Cota Parlamentar',
      data_empenho: toISODate(raw.data || raw.dataDocumento),
      valor_empenhado: toNumber(raw.valor || raw.valorLiquido || 0),
      favorecido_nome: raw.fornecedor || raw.nomeFornecedor || 'NAO INFORMADO',
      favorecido_cnpj_cpf: String(raw.cnpjCpf || '').replace(/\D/g, ''),
      elemento_despesa: 'CEAPS',
      fonte_recurso: 'Cota para Exercicio da Atividade Parlamentar',
      funcao_governo: 'Legislativo',
      numero_empenho: String(raw.documento || ''),
      municipio_nome: 'Brasilia',
      municipio_ibge: '5300108',
      uf: 'DF',
      fornecedor_sistema: 'Senado API',
      url_origem: 'https://www12.senado.leg.br/dados-abertos',
      atualizado_em: new Date().toISOString(),
      payload_origem: raw
    }
  });
}

return out;
