// n8n Code Node - Normalizador de despesas de Ministerios (Executivo Federal)
// Entrada: itens da API do Portal da Transparencia em item.json (registro individual)

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
  const idBase = raw.id || raw.numeroDocumento || raw.codigoDocumento || `${raw.data || 'sem_data'}:${raw.valor || 0}`;
  out.push({
    json: {
      id_transacao: `ministerio:${idBase}`,
      fonte_id: raw.fonte_id || null,
      categoria_origem: 'Executivo Federal',
      agente_publico: raw.nomeOrgaoSuperior || raw.ministerio || null,
      partido: null,
      tipo_despesa: raw.categoriaDespesa || raw.elementoDespesa || raw.descricao || null,
      data_empenho: toISODate(raw.data || raw.dataDocumento || raw.dataEmissao),
      valor_empenhado: toNumber(raw.valor || raw.valorEmpenhado || raw.valorPago || 0),
      favorecido_nome: raw.favorecido || raw.nomeFavorecido || raw.fornecedor || 'NAO INFORMADO',
      favorecido_cnpj_cpf: String(raw.cpfCnpj || raw.documentoFavorecido || '').replace(/\D/g, ''),
      elemento_despesa: raw.elementoDespesa || null,
      fonte_recurso: raw.fonteRecurso || null,
      funcao_governo: raw.funcao || 'Executivo',
      numero_empenho: String(raw.numeroEmpenho || raw.numeroDocumento || ''),
      municipio_nome: 'Brasilia',
      municipio_ibge: '5300108',
      uf: 'DF',
      fornecedor_sistema: 'Portal Transparencia API',
      url_origem: 'https://api.portaldatransparencia.gov.br',
      atualizado_em: new Date().toISOString(),
      payload_origem: raw
    }
  });
}

return out;
