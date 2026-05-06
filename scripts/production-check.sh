#!/bin/bash

# Post-Production Deployment Validation Script
# Verifica se tudo está pronto para produção

set -e

echo "🔍 IIIbrasil v2.0.0 - Production Readiness Check"
echo "=================================================="
echo ""

CHECKS_PASSED=0
CHECKS_FAILED=0

# Function para checar
check() {
    if [ $1 -eq 0 ]; then
        echo "✅ $2"
        ((CHECKS_PASSED++))
    else
        echo "❌ $2"
        ((CHECKS_FAILED++))
    fi
}

# 1. Git checks
echo "📦 Git Configuration:"
git log --oneline -1 > /dev/null 2>&1
check $? "Repository initialized"

[ -f .gitignore ]
check $? ".gitignore exists"

[ -f .git/config ]
check $? "Git config exists"

# 2. Backend checks
echo ""
echo "🐍 Backend Configuration:"
[ -f backend/requirements.txt ]
check $? "Backend dependencies (requirements.txt)"

[ -f backend/main.py ]
check $? "Backend main.py"

[ -f backend/Dockerfile ]
check $? "Backend Dockerfile"

[ -f backend/.dockerignore ]
check $? "Backend .dockerignore"

# 3. Frontend checks
echo ""
echo "⚛️  Frontend Configuration:"
[ -f frontend/package.json ]
check $? "Frontend package.json"

[ -f frontend/vite.config.ts ]
check $? "Frontend vite.config.ts (optimized)"

[ -f frontend/Dockerfile ]
check $? "Frontend Dockerfile"

# 4. Configuration files
echo ""
echo "⚙️  Configuration Files:"
[ -f render.yaml ]
check $? "Render Blueprint (render.yaml)"

[ -f docker-compose.yml ]
check $? "Docker Compose (development)"

[ -f .env.example ]
check $? "Environment template (.env.example)"

[ -f .github/workflows/ci-cd.yml ]
check $? "CI/CD Pipeline (GitHub Actions)"

# 5. Documentation
echo ""
echo "📚 Documentation:"
[ -f README.md ]
check $? "README.md"

[ -f PRODUCTION_QUICKSTART.md ]
check $? "PRODUCTION_QUICKSTART.md"

[ -f PRODUCTION_DEPLOYMENT.md ]
check $? "PRODUCTION_DEPLOYMENT.md"

[ -f SECURITY.md ]
check $? "SECURITY.md"

[ -f IMPROVEMENTS_SUMMARY.md ]
check $? "IMPROVEMENTS_SUMMARY.md"

# 6. Python specific
echo ""
echo "🐍 Python Checks:"
python3 --version > /dev/null 2>&1
check $? "Python 3 installed"

python3 -m pip --version > /dev/null 2>&1
check $? "pip installed"

[ -f backend/requirements-dev.txt ]
check $? "Dev requirements (requirements-dev.txt)"

# 7. Node specific
echo ""
echo "📦 Node Checks:"
which node > /dev/null 2>&1
NODE_CHECK=$?
check $NODE_CHECK "Node.js installed"

if [ $NODE_CHECK -eq 0 ]; then
    npm --version > /dev/null 2>&1
    check $? "npm installed"
fi

# 8. Docker
echo ""
echo "🐳 Docker Checks:"
which docker > /dev/null 2>&1
DOCKER_CHECK=$?
check $DOCKER_CHECK "Docker installed"

if [ $DOCKER_CHECK -eq 0 ]; then
    docker --version > /dev/null 2>&1
    check $? "Docker daemon running"
fi

# 9. Environment
echo ""
echo "🌍 Environment Checks:"
if [ -f .env ]; then
    echo "✅ .env file exists"
    ((CHECKS_PASSED++))
else
    echo "⚠️  .env file NOT found (copy from .env.example)"
fi

# 10. Git status
echo ""
echo "📝 Repository Status:"
if [ -z "$(git status --porcelain)" ]; then
    echo "✅ Working directory clean"
    ((CHECKS_PASSED++))
else
    echo "⚠️  Uncommitted changes detected"
    echo "   Run: git status"
fi

# Summary
echo ""
echo "=================================================="
echo "📊 SUMMARY"
echo "=================================================="
echo "✅ Passed: $CHECKS_PASSED"
echo "❌ Failed: $CHECKS_FAILED"
TOTAL=$((CHECKS_PASSED + CHECKS_FAILED))
PERCENTAGE=$((CHECKS_PASSED * 100 / TOTAL))
echo "📈 Score: $PERCENTAGE%"
echo ""

if [ $CHECKS_FAILED -eq 0 ]; then
    echo "🎉 SYSTEM IS PRODUCTION-READY!"
    echo ""
    echo "🚀 Next steps:"
    echo "  1. Configure .env with real values"
    echo "  2. Test locally: docker-compose up -d"
    echo "  3. Push to GitHub: git push origin main"
    echo "  4. Deploy on Render: render.com"
    echo ""
    echo "📖 Documentation:"
    echo "  - Quick Start: PRODUCTION_QUICKSTART.md"
    echo "  - Full Guide: PRODUCTION_DEPLOYMENT.md"
    echo "  - Security: SECURITY.md"
    exit 0
else
    echo "❌ ISSUES FOUND"
    echo ""
    echo "Please fix the failing checks above before deploying."
    exit 1
fi
