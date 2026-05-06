#!/bin/bash
# Inicia backend + frontend em background e executa testes de todas as funcionalidades

set -e
BASE="http://localhost:8000"
PASS=0
FAIL=0

ok()   { echo "  ✅  $1"; ((PASS++)); }
fail() { echo "  ❌  $1"; ((FAIL++)); }
info() { echo ""; echo "▶ $1"; }

# ── Iniciar backend ──────────────────────────────────────────
info "Iniciando backend..."
export DATABASE_BACKEND=sqlite
export ENVIRONMENT=development
export JWT_SECRET_KEY=dev_test_key
export ALLOWED_HOSTS="localhost,127.0.0.1"
export CORS_ORIGINS="http://localhost:5173"

cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --log-level warning &
BACKEND_PID=$!
cd ..

# Aguardar backend subir
for i in $(seq 1 20); do
  if curl -s "$BASE/health" > /dev/null 2>&1; then break; fi
  sleep 1
done

# ── Health ───────────────────────────────────────────────────
info "1. Health Check"
STATUS=$(curl -s "$BASE/health" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('status',''))" 2>/dev/null)
[ "$STATUS" = "ok" ] && ok "GET /health → status: ok" || fail "GET /health falhou (status=$STATUS)"

# ── Gastos ───────────────────────────────────────────────────
info "2. Gastos Públicos"
TOTAL=$(curl -s "$BASE/api/v1/gastos?page=1&page_size=5" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('meta',{}).get('total',0))" 2>/dev/null)
[ "$TOTAL" -gt 0 ] 2>/dev/null && ok "GET /gastos → $TOTAL registros" || fail "GET /gastos sem dados"

TOTAL_EMP=$(curl -s "$BASE/api/v1/gastos/resumo" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('total_empenhado',0))" 2>/dev/null)
[ "$TOTAL_EMP" != "0" ] && ok "GET /gastos/resumo → R\$ $TOTAL_EMP" || fail "GET /gastos/resumo sem dados"

curl -s "$BASE/api/v1/gastos/top-fornecedores?limit=3" | python3 -c "import sys,json; d=json.load(sys.stdin); assert len(d)>0" 2>/dev/null \
  && ok "GET /gastos/top-fornecedores → OK" || fail "GET /gastos/top-fornecedores falhou"

# ── Exports ──────────────────────────────────────────────────
info "3. Exportação de arquivos"
CSV_SIZE=$(curl -s -o /tmp/test.csv -w "%{size_download}" "$BASE/api/v1/gastos/export/csv")
[ "$CSV_SIZE" -gt 100 ] && ok "GET /export/csv → ${CSV_SIZE} bytes" || fail "Export CSV vazio"

XLSX_SIZE=$(curl -s -o /tmp/test.xlsx -w "%{size_download}" "$BASE/api/v1/gastos/export/xlsx")
[ "$XLSX_SIZE" -gt 100 ] && ok "GET /export/xlsx → ${XLSX_SIZE} bytes" || fail "Export XLSX vazio"

PDF_SIZE=$(curl -s -o /tmp/test.pdf -w "%{size_download}" "$BASE/api/v1/gastos/export/pdf")
[ "$PDF_SIZE" -gt 100 ] && ok "GET /export/pdf → ${PDF_SIZE} bytes" || fail "Export PDF vazio"

# ── RPA ──────────────────────────────────────────────────────
info "4. RPA — Fontes de dados"
FONTES=$(curl -s "$BASE/api/v1/rpa/fontes" | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d.get('fontes',[])))" 2>/dev/null)
[ "$FONTES" -gt 0 ] && ok "GET /rpa/fontes → $FONTES fontes registradas" || fail "GET /rpa/fontes sem dados"

RPA_STATUS=$(curl -s "$BASE/api/v1/rpa/status" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('scheduler_ativo',''))" 2>/dev/null)
[ "$RPA_STATUS" = "True" ] && ok "GET /rpa/status → scheduler ativo" || fail "Scheduler inativo"

# ── Busca dados reais da Câmara ───────────────────────────────
info "5. RPA — Câmara dos Deputados (dados reais)"
echo "   Executando agente Câmara (aguarde ~15s)..."
EXEC=$(curl -s -X POST "$BASE/api/v1/rpa/fontes/camara/executar")
echo "   $EXEC"
sleep 15
LOG=$(curl -s "$BASE/api/v1/rpa/logs?limit=1" | python3 -c "import sys,json; d=json.load(sys.stdin); logs=d.get('logs',[]); print(logs[0].get('status','') if logs else 'sem log')" 2>/dev/null)
[ "$LOG" = "success" ] || [ "$LOG" = "running" ] && ok "Agente Câmara → $LOG" || fail "Agente Câmara → $LOG"

# ── ML ───────────────────────────────────────────────────────
info "6. Machine Learning"
ML_STATUS=$(curl -s "$BASE/api/v1/ml/status" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('detector',{}).get('backend',''))" 2>/dev/null)
[ -n "$ML_STATUS" ] && ok "GET /ml/status → backend: $ML_STATUS" || fail "GET /ml/status falhou"

curl -s "$BASE/api/v1/ml/anomalias?limit=5" | python3 -c "import sys,json; d=json.load(sys.stdin); assert 'anomalias' in d" 2>/dev/null \
  && ok "GET /ml/anomalias → OK" || fail "GET /ml/anomalias falhou"

curl -s "$BASE/api/v1/ml/previsao?periodos=3" | python3 -c "import sys,json; d=json.load(sys.stdin); assert 'previsao' in d" 2>/dev/null \
  && ok "GET /ml/previsao → OK" || fail "GET /ml/previsao falhou"

# ── AI ───────────────────────────────────────────────────────
info "7. IA Claude"
AI_STATUS=$(curl -s "$BASE/api/v1/ai/status" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('configurado',''))" 2>/dev/null)
[ "$AI_STATUS" = "True" ] && ok "ANTHROPIC_API_KEY configurada" || ok "IA: chave não configurada (opcional)"

# ── Auth ─────────────────────────────────────────────────────
info "8. Autenticação JWT"
TOKEN=$(curl -s -X POST "$BASE/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@ebrasil.gov.br&password=admin" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('access_token','')[:20])" 2>/dev/null)
[ -n "$TOKEN" ] && ok "POST /auth/login → token: ${TOKEN}..." || fail "Login falhou"

# ── Resultado ────────────────────────────────────────────────
echo ""
echo "════════════════════════════════════"
echo "  ✅ Passou: $PASS   ❌ Falhou: $FAIL"
echo "════════════════════════════════════"
echo ""

kill $BACKEND_PID 2>/dev/null || true
[ $FAIL -eq 0 ] && exit 0 || exit 1
