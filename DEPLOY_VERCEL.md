# 🚀 Deploy no Vercel

Guia rápido para fazer deploy do eBrasil Transparência no Vercel.

## O que é Vercel?

- Plataforma perfeita para aplicações React/Next.js estáticas e serverless
- Deploy automático a partir do GitHub
- Domínio gratuito `.vercel.app` ou seu próprio domínio
- Suporte a variáveis de ambiente

## Pré-requisitos

1. Conta no [Vercel](https://vercel.com) (free)
2. Repositório GitHub com este projeto
3. URL do backend em produção (ex: `https://seu-backend.onrender.com`)

## Passo 1: Preparar o GitHub

```bash
# Commit das alterações
git add .
git commit -m "chore: add Vercel configuration"
git push origin main
```

## Passo 2: Conectar ao Vercel

1. Acesse [vercel.com/new](https://vercel.com/new)
2. Clique em **Import Git Repository**
3. Conecte sua conta GitHub
4. Selecione o repositório `ebrasil`

## Passo 3: Configurar o Projeto

Na tela de importação:

### Root Directory (Importante!)
- Deixe em branco (Vercel vai auto-detectar pelo `vercel.json`)
- OU selecione manualmente: `frontend`

### Environment Variables

Adicione as variáveis obrigatórias:

```
VITE_API_BASE_URL = https://seu-backend.onrender.com
```

Onde `seu-backend.onrender.com` é a URL real do seu backend em produção.

### Build & Output Settings

Devem estar pré-preenchidas (Vercel vai ler do `vercel.json`):
- **Build Command**: `cd frontend && npm install && npm run build`
- **Output Directory**: `frontend/dist`

## Passo 4: Deploy

1. Clique em **Deploy**
2. Aguarde 2-5 minutos
3. Vercel vai:
   - Clonar o repositório
   - Instalar dependências
   - Executar o build
   - Gerar URL de produção

## Passo 5: Validar

Após o deploy bem-sucedido:

```bash
# URL padrão (gerada automaticamente)
https://seu-projeto.vercel.app

# Testes
curl https://seu-projeto.vercel.app/
curl https://seu-projeto.vercel.app/api/v1/gastos
```

## Domínio Personalizado

Para adicionar seu próprio domínio:

1. No projeto Vercel → **Settings** → **Domains**
2. Adicione seu domínio (ex: `transparencia.com.br`)
3. Siga as instruções para atualizar DNS no registrador

## Atualizar Configurações

### Adicionar/Alterar Variáveis de Ambiente

1. Vá para **Settings** → **Environment Variables**
2. Adicione ou modifique variáveis
3. Clique em **Deploy** novamente para usar as novas variáveis

### Problemas Comuns

#### ❌ Build falha com "Module not found"

**Solução**: Vercel está tentando buildar o backend também. Verifique:

```bash
# Certifique-se que o vercel.json está correto
cat vercel.json

# E que .vercelignore existe
cat .vercelignore
```

#### ❌ CORS Error (Frontend não consegue chamar Backend)

**Solução**: Atualize a variável `VITE_API_BASE_URL`:

1. Vá para **Settings** → **Environment Variables**
2. Mude `VITE_API_BASE_URL` para o URL correto do backend
3. Faça um novo deploy

#### ❌ "Cannot find module 'react'"

**Solução**: Pode ser que `node_modules` foi deletado. Desative o cache:

1. **Settings** → **Git**
2. Clique em **Clear Build Cache**
3. Faça um novo deploy

## CI/CD Automático

Após o setup inicial, toda vez que você fizer `git push origin main`:

1. Vercel detecta a mudança automaticamente
2. Inicia um novo build
3. Se passar nos testes, faz deploy automático
4. A URL continua a mesma

### Desabilitar Deploy Automático

Se quiser fazer deploy manualmente:

1. **Settings** → **Git** 
2. Desabilite **Automatic Deployments**
3. Use o botão **Deploy** no dashboard quando quiser

## Backend em Produção

Este setup assume que o **backend** já está rodando em outro lugar:

- **Render**: `https://seu-backend.onrender.com` ✅ (recomendado)
- **Railway**: `https://seu-backend.railway.app`
- **AWS**: Seu URL customizado
- **Outro**: Sua URL

> Se o backend ainda não está em produção, complete o [DEPLOY_RENDER.md](./DEPLOY_RENDER.md) primeiro.

## Analytics e Logs

Monitorar seu projeto:

1. Dashboard Vercel → seu projeto
2. **Analytics** → veja performance, requisições, localização
3. **Logs** → veja erros em produção

## Rollback (Voltar versão anterior)

Se algo der errado:

1. Vá para **Deployments**
2. Clique nos 3 pontos do último deployment OK
3. Selecione **Promote to Production**

## Custo

- **Free tier**: ✅ Perfeito para este projeto
  - Deploy ilimitado
  - 50GB banda/mês
  - Analytics básico
  - Suporta até ~3-5 requisições simultâneas

- **Pro**: Se precisar de mais banda ou recursos

## Próximos Passos

✅ Deploy do frontend no Vercel
- [ ] Configurar domínio personalizado
- [ ] Monitorar performance nos Analytics
- [ ] Configurar email de notificação para erros
- [ ] Documentar URL em produção no README

---

**Dúvidas?** Consulte:
- [Vercel Docs](https://vercel.com/docs)
- [Vite Deployment Guides](https://vitejs.dev/guide/static-deploy.html)
