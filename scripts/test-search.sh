#!/bin/bash

# Interactive Search & File Query Testing Script
# Tests all search endpoints after production deployment

set -e

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔍 IIIbrasil - Search & Query Testing"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Configuration
API_URL="${1:-http://localhost:8000}"
PASSED=0
FAILED=0
SKIPPED=0

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper function to test endpoint
test_endpoint() {
    local name=$1
    local method=$2
    local endpoint=$3
    local expected_code=$4
    
    echo -n "Testing: $name ... "
    
    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" "$API_URL$endpoint")
        http_code=$(echo "$response" | tail -n1)
        body=$(echo "$response" | head -n-1)
    else
        response=$(curl -s -w "\n%{http_code}" -X "$method" "$API_URL$endpoint")
        http_code=$(echo "$response" | tail -n1)
        body=$(echo "$response" | head -n-1)
    fi
    
    if [ "$http_code" = "$expected_code" ] || [[ "$expected_code" == *"$http_code"* ]]; then
        echo -e "${GREEN}✓ PASS${NC} (HTTP $http_code)"
        ((PASSED++))
        
        # Print sample of response
        if [ -z "$body" ]; then
            echo "  Response: (empty)"
        else
            sample=$(echo "$body" | head -c 100)
            if [ ${#body} -gt 100 ]; then
                echo "  Response: $sample..."
            else
                echo "  Response: $sample"
            fi
        fi
    else
        echo -e "${RED}✗ FAIL${NC} (HTTP $http_code, expected $expected_code)"
        echo "  Response: $body"
        ((FAILED++))
    fi
    echo ""
}

# Helper to test search with params
test_search() {
    local name=$1
    local endpoint=$2
    
    echo -n "🔎 Search: $name ... "
    
    response=$(curl -s -w "\n%{http_code}" "$API_URL/api/v1$endpoint")
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)
    
    if [ "$http_code" = "200" ]; then
        count=$(echo "$body" | jq 'if type == "array" then length elif .items then (.items | length) elif .meta then .meta.total else 0 end' 2>/dev/null || echo "?")
        echo -e "${GREEN}✓ OK${NC} - Found $count items"
        ((PASSED++))
    else
        echo -e "${RED}✗ FAIL${NC} (HTTP $http_code)"
        ((FAILED++))
    fi
    echo ""
}

# ============================================================================
# 1. HEALTH CHECK
# ============================================================================

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}1️⃣  HEALTH CHECK${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

test_endpoint "API Health" "GET" "/health" "200"

# ============================================================================
# 2. BASIC SEARCH ENDPOINTS
# ============================================================================

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}2️⃣  BASIC SEARCH${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

test_search "All Gastos" "/gastos?page_size=10"
test_search "Gastos with Pagination" "/gastos?page=1&page_size=20"
test_search "Resumo de Gastos" "/gastos/resumo"
test_search "Top Fornecedores" "/gastos/top-fornecedores?limit=5"

# ============================================================================
# 3. FILTER TESTS - BY LOCATION
# ============================================================================

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}3️⃣  FILTER BY LOCATION${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

test_search "Filter by UF (SP)" "/gastos?uf=SP&page_size=20"
test_search "Filter by UF (RJ)" "/gastos?uf=RJ&page_size=20"
test_search "Filter by UF (MG)" "/gastos?uf=MG&page_size=20"
test_search "Filter by UF (BA)" "/gastos?uf=BA&page_size=20"

# ============================================================================
# 4. FILTER TESTS - BY DATE
# ============================================================================

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}4️⃣  FILTER BY DATE${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

test_search "Year 2023" "/gastos?data_inicio=2023-01-01&data_fim=2023-12-31&page_size=20"
test_search "Year 2024" "/gastos?data_inicio=2024-01-01&data_fim=2024-12-31&page_size=20"
test_search "Single Month" "/gastos?data_inicio=2023-01-01&data_fim=2023-01-31&page_size=20"

# ============================================================================
# 5. FILTER TESTS - BY CRITERIA
# ============================================================================

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}5️⃣  FILTER BY CRITERIA${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

test_search "Search Fornecedor" "/gastos?fornecedor=empresa&page_size=20"
test_search "By Categoria" "/gastos?categoria_origem=camera&page_size=20"
test_search "By Agente" "/gastos?agente_publico=senador&page_size=20"
test_search "By Partido" "/gastos?partido=PT&page_size=20"

# ============================================================================
# 6. COMBINED FILTERS
# ============================================================================

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}6️⃣  COMBINED FILTERS${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

test_search "UF + Date" "/gastos?uf=SP&data_inicio=2023-01-01&data_fim=2023-12-31&page_size=20"
test_search "UF + Fornecedor" "/gastos?uf=RJ&fornecedor=empresa&page_size=20"
test_search "Date + Categoria" "/gastos?data_inicio=2023-01-01&data_fim=2023-12-31&categoria_origem=camera&page_size=20"
test_search "Multiple Filters" "/gastos?uf=MG&data_inicio=2023-01-01&data_fim=2023-12-31&categoria_origem=camera&page_size=20"

# ============================================================================
# 7. STATISTICS
# ============================================================================

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}7️⃣  STATISTICS ENDPOINTS${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

test_search "Stats por Função" "/stats/por-funcao"
test_search "Stats por UF" "/stats/por-uf"
test_search "Stats por Categoria" "/stats/por-categoria"
test_search "Evolução Mensal" "/stats/evolucao-mensal"
test_search "Stats por Elemento" "/stats/por-elemento"
test_search "Stats por Partido" "/stats/por-partido"

# ============================================================================
# 8. EXPORT
# ============================================================================

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}8️⃣  EXPORT TESTS${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

test_endpoint "Export as CSV" "GET" "/api/v1/gastos/export/csv" "200"
test_endpoint "Export with Filter" "GET" "/api/v1/gastos/export/csv?uf=SP&page_size=50" "200"

# ============================================================================
# 9. ERROR CASES
# ============================================================================

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}9️⃣  ERROR HANDLING${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

test_endpoint "Invalid UF (too long)" "GET" "/api/v1/gastos?uf=ABC" "422"
test_endpoint "Invalid IBGE (too short)" "GET" "/api/v1/gastos?municipio_ibge=123" "422"
test_endpoint "Invalid page (negative)" "GET" "/api/v1/gastos?page=-1" "422"
test_endpoint "Invalid page_size (too large)" "GET" "/api/v1/gastos?page_size=500" "422"
test_endpoint "Nonexistent endpoint" "GET" "/api/v1/invalid" "404"

# ============================================================================
# 10. PERFORMANCE
# ============================================================================

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🔟 PERFORMANCE${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

echo -n "Response time for simple query ... "
start=$(date +%s%N)
curl -s "$API_URL/api/v1/gastos?page_size=10" > /dev/null
end=$(date +%s%N)
duration=$((($end - $start) / 1000000))
echo "${GREEN}${duration}ms${NC}"

if [ $duration -lt 1000 ]; then
    echo -e "  Status: ${GREEN}✓ Under 1s${NC}"
    ((PASSED++))
else
    echo -e "  Status: ${YELLOW}⚠ Over 1s${NC}"
    ((FAILED++))
fi
echo ""

# ============================================================================
# SUMMARY
# ============================================================================

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}📊 TEST SUMMARY${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

TOTAL=$((PASSED + FAILED))
PERCENTAGE=$((PASSED * 100 / TOTAL))

echo -e "Passed:  ${GREEN}✓ $PASSED${NC}"
echo -e "Failed:  ${RED}✗ $FAILED${NC}"
echo -e "Total:   $TOTAL"
echo -e "Score:   $PERCENTAGE%"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 ALL TESTS PASSED!${NC}"
    exit 0
else
    echo -e "${RED}⚠️  SOME TESTS FAILED${NC}"
    exit 1
fi
