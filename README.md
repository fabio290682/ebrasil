# 🇧🇷 IIIbrasil — Transparência BR v2.0.0

**Plataforma de consulta de gastos públicos integrados — Schema Único**

![CI/CD Status](https://github.com/seu-repo/ebrasil/actions/workflows/ci-cd.yml/badge.svg)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/)
[![React](https://img.shields.io/badge/react-19-blue.svg)](https://react.dev)

---

## 📚 Documentação Principal

### 🚀 Começar em Produção
- **[PRODUCTION_QUICKSTART.md](./PRODUCTION_QUICKSTART.md)** - 5 passos para deploy em 10 minutos ⭐
- **[IMPROVEMENTS_SUMMARY.md](./IMPROVEMENTS_SUMMARY.md)** - O que foi melhorado na v2.0.0

### 📋 Guias Detalhados
- **[PRODUCTION_DEPLOYMENT.md](./PRODUCTION_DEPLOYMENT.md)** - Guia completo de deployment
- **[SECURITY.md](./SECURITY.md)** - Headers de segurança, OWASP compliance
- **[DEPLOY_RENDER.md](./DEPLOY_RENDER.md)** - Render-specific
- **[infraestrutura_aws.md](./infraestrutura_aws.md)** - AWS-specific

### 💾 Frontend & Backend
- **[backend/README_BACKEND.md](./backend/README_BACKEND.md)** - API documentation
- **[frontend/README.md](./frontend/README.md)** - Frontend setup
- **[n8n/README.md](./n8n/README.md)** - Workflows & automação

---

## 🏗️ Arquitetura

```
┌─────────────────────────────────┐
│   Frontend (React + TypeScript)  │  ← Render Static
├─────────────────────────────────┤
│   Backend (FastAPI + Python)     │  ← Render Web Service
├─────────────────────────────────┤
│   Databases & Cache              │
│   - SQLite / MongoDB             │
│   - Redis (cache)                │
│   - PostgreSQL (n8n)             │
└─────────────────────────────────┘
```

---

## ⚡ Quick Start

### Desenvolvimento Local

```bash
# 1. Clone
git clone https://github.com/seu-repo/ebrasil.git
cd ebrasil

# 2. Ambiente
cp .env.example .env
# Editar .env com suas variáveis

# 3. Docker (recomendado)
docker-compose up -d

# 4. Verificar
curl http://localhost:8000/health
open http://localhost:5173
```

### Produção (Render)

```bash
# 1. Push para main
git push origin main

# 2. No Render.com:
#    New → Blueprint → Connect GitHub
#    Deploy automático via CI/CD

# 3. Validar
curl https://seu-api.onrender.com/health
```

---

## 📦 Stack Técnico

### Backend
- **FastAPI** 0.115 - Web framework
- **SQLAlchemy** 2.0 - ORM
- **Pydantic** 2.9 - Validation
- **PyMongo** 4.10 - MongoDB
- **Uvicorn** 0.30 - ASGI server
- **Redis** - Caching
- **structlog** - JSON logging

### Frontend
- **React** 19 - UI framework
- **TypeScript** 5.9 - Type safety
- **Vite** 8 - Build tool
- **TailwindCSS** - Styling

### DevOps
- **Docker** - Containerização
- **GitHub Actions** - CI/CD
- **Render** - Hosting (recomendado)
- **AWS** - Alternative hosting

---

## 🚀 Melhorias v2.0.0

✅ **Performance**
- Compressão GZIP (-70% bandwidth)
- Bundle otimizado (-52% JS size)
- Multi-stage Docker builds (-30% image size)
- Logging estruturado

✅ **Segurança**
- Rate limiting
- OWASP headers (HSTS, CSP, X-Frame-Options)
- Trusted host validation
- Input/output sanitization

✅ **DevOps**
- CI/CD pipeline (GitHub Actions)
- Docker compose para dev
- Health checks robustos
- Deploy automático

✅ **Documentação**
- Guia de produção
- Security checklist
- Deployment procedures
- Troubleshooting

---

## 🔐 Segurança

- ✅ HTTPS obrigatório
- ✅ CORS restrictivo
- ✅ Rate limiting (100 req/min)
- ✅ JWT authentication
- ✅ SQL injection protection (ORM)
- ✅ XSS protection (CSP)
- ✅ Dependency scanning (GitHub)

Ver [SECURITY.md](./SECURITY.md) para detalhes.

---

## 📊 Status

| Componente | Status | Link |
|-----------|--------|------|
| Backend | ✅ Production Ready | `/api/v1` |
| Frontend | ✅ Production Ready | `/` |
| CI/CD | ✅ Configured | `.github/workflows/ci-cd.yml` |
| Database | ✅ Automated | SQLite / MongoDB |
| Monitoring | ✅ Structured Logging | JSON output |

---

## 🤝 Contribuindo

```bash
# 1. Fork & clone
git clone https://github.com/SEU-USER/ebrasil.git
cd ebrasil

# 2. Create branch
git checkout -b feature/sua-feature

# 3. Develop & test
docker-compose up -d
# ... faça suas mudanças

# 4. Commit
git commit -m "feat: descrição"

# 5. Push
git push origin feature/sua-feature

# 6. Pull Request
# Abra PR no GitHub
```

---

## 📝 Licença

MIT License - veja [LICENSE](./LICENSE) para detalhes.

---

## 🔗 Links Úteis

- **Render Dashboard**: https://render.com/dashboard
- **GitHub Workflows**: .github/workflows/
- **API Docs**: https://seu-api.onrender.com/docs
- **Redoc**: https://seu-api.onrender.com/redoc
- **Status**: https://status.example.com

---

## 💬 Suporte

- 📖 **Documentação**: Veja `*.md` neste diretório
- 🐛 **Issues**: [GitHub Issues](https://github.com/seu-repo/ebrasil/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/seu-repo/ebrasil/discussions)

---

## 📈 Roadmap

- [ ] v2.1 - Redis distribuído
- [ ] v2.2 - 2FA Authentication
- [ ] v2.3 - GraphQL endpoint
- [ ] v3.0 - Mobile app
- [ ] v3.1 - Real-time WebSockets
- [ ] v3.2 - Advanced Analytics

---

## 🎯 Próximos Passos

1. **Ler**: [PRODUCTION_QUICKSTART.md](./PRODUCTION_QUICKSTART.md)
2. **Configurar**: `.env` com suas variáveis
3. **Testar**: `docker-compose up -d`
4. **Deploy**: `git push origin main`
5. **Monitorar**: Logs e health checks

---

**Versão**: 2.0.0  
**Status**: ✅ Production Ready  
**Última atualização**: 2026-04-26

Made with ❤️ for Brazilian Transparency
