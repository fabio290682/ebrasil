// n8n Code Node - Normalizador CEAP (Camara dos Deputados)
// Entrada: itens da API da Camara em item.json (registro individual)

function toISODate(v) {
  if (!v) return null;
  const s = String(v);
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
  const idBase = raw.codDocumento || raw.numDocumento || raw.urlDocumento || raw.id;
  const id = `camara:${idBase || `${raw.dataDocumento || 'sem_data'}:${raw.valorLiquido || 0}`}`;

  out.push({
    json: {
      id_transacao: id,
      fonte_id: raw.fonte_id || null,
      categoria_origem: 'Legislativo Federal',
      agente_publico: raw.nomeParlamentar || raw.nomeDeputado || null,
      partido: raw.siglaPartido || null,
      tipo_despesa: raw.tipoDespesa || raw.descricao || 'Cota Parlamentar',
      data_empenho: toISODate(raw.dataDocumento || raw.dataEmissao || raw.anoMes),
      valor_empenhado: toNumber(raw.valorLiquido ?? raw.valorDocumento ?? raw.valorGlosa ?? 0),
      favorecido_nome: raw.nomeFornecedor || raw.fornecedor || 'NAO INFORMADO',
      favorecido_cnpj_cpf: String(raw.cnpjCpfFornecedor || '').replace(/\D/g, ''),
      elemento_despesa: 'CEAP',
      fonte_recurso: 'Cota para Exercicio da Atividade Parlamentar',
      funcao_governo: 'Legislativo',
      numero_empenho: String(raw.numDocumento || raw.codDocumento || ''),
      municipio_nome: 'Brasilia',
      municipio_ibge: '5300108',
      uf: 'DF',
      fornecedor_sistema: 'Camara API',
      url_origem: 'https://dadosabertos.camara.leg.br/api/v2',
      atualizado_em: new Date().toISOString(),
      payload_origem: raw
    }
  });
}

return out;
