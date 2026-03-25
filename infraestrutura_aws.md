# Infraestrutura AWS — Super-Integrador de Transparência
## Diagrama de Arquitetura e Estimativa de Custo

---

## Visão Geral da Infraestrutura

```
┌─────────────────────────────────────────────────────────────────┐
│                        AWS Cloud                                │
│                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────┐  │
│  │   EC2 t3.small│    │  EC2 Spot    │    │   S3 Data Lake   │  │
│  │   Airflow     │───▶│  Scrapers    │───▶│   (Zona Bruta)   │  │
│  │  $15/mês     │    │  $5-20/mês   │    │  ~$5/mês (100GB) │  │
│  └──────────────┘    └──────────────┘    └────────┬─────────┘  │
│                                                   │             │
│  ┌──────────────┐    ┌──────────────┐    ┌────────▼─────────┐  │
│  │  ElasticSearch│    │    Redis     │    │  Redshift (DW)   │  │
│  │  (Buscas)    │◀───│   (Cache)    │◀───│  (Dados prontos) │  │
│  │  ~$40/mês    │    │  ~$15/mês    │    │  ~$60/mês        │  │
│  └──────┬───────┘    └──────────────┘    └──────────────────┘  │
│         │                                                        │
│  ┌──────▼───────┐    ┌──────────────┐    ┌──────────────────┐  │
│  │  API Gateway │    │  Lambda      │    │   CloudWatch     │  │
│  │  + FastAPI   │───▶│  (Alertas)   │    │   (Monitoramento)│  │
│  │  ~$10/mês    │    │  ~$1/mês     │    │  ~$5/mês         │  │
│  └──────────────┘    └──────────────┘    └──────────────────┘  │
└─────────────────────────────────────────────────────────────────┘

                    CUSTO ESTIMADO TOTAL: ~$151-250/mês
                    (Fase MVP — Federal + Capitais)
```

---

## Detalhamento por Serviço

### 1. EC2 — Computação

#### Airflow Scheduler (orquestrador)
- **Instância:** t3.small (2 vCPUs, 2GB RAM)
- **Uso:** 24/7 (sempre ligado)
- **Custo:** ~$15/mês
- **Por quê esta instância:** O Airflow só precisa acordar os workers, não processa dados diretamente. Uma instância pequena basta.

#### EC2 Spot — Scrapers e Transformações
- **Instância:** c5.xlarge (4 vCPUs, 8GB RAM) como Spot Instance
- **Uso:** ~6 horas/dia (coleta noturna)
- **Custo:** ~$5-20/mês (Spot pode ser interrompida — Airflow reprocessa automaticamente)
- **Por quê Spot:** Tarefas de coleta toleram interrupção. Economia de até 70% vs On-Demand.

#### API Server (FastAPI)
- **Instância:** t3.medium (2 vCPUs, 4GB RAM) com Auto Scaling
- **Uso:** 24/7 com scaling entre 1-3 instâncias
- **Custo:** ~$30-60/mês
- **Por quê Auto Scaling:** Escala para 3 instâncias no horário comercial e reduz para 1 à noite.

---

### 2. S3 — Data Lake (Armazenamento de Objetos)

```
Estrutura de buckets:
  transparencia-br-raw/           ← Dados brutos (como vieram da fonte)
    federal/2024/06/01/dados.json
    betha/4205407/2024/06/01/dados.json
    
  transparencia-br-processed/     ← Dados padronizados
    gastos_publicos/2024/06/dados.parquet
    
  transparencia-br-archive/       ← Dados com mais de 1 ano (Glacier)
    2022/...
    2023/...
```

#### Estimativa de volume:
- Federal: ~500MB/mês
- Capitais (27): ~200MB/mês
- Municípios via scraping: ~300MB/mês
- **Total acumulado em 1 ano:** ~12GB (muito barato no S3)

#### Política de lifecycle (automática):
```
0-30 dias:    S3 Standard         = $0.023/GB  → ~$0.30/mês
31-365 dias:  S3 Infrequent Access = $0.0125/GB → ~$0.10/mês
365+ dias:    S3 Glacier Instant   = $0.004/GB  → ~$0.05/mês
```

**Custo estimado S3:** ~$5-10/mês

---

### 3. Redshift Serverless — Data Warehouse

- **Configuração:** Serverless (paga só pelo que usa)
- **RPU (Redshift Processing Units):** 8 RPU mínimo → 128 RPU máximo
- **Custo:** $0.36/RPU-hora
- **Uso estimado:** 4 horas/dia de processamento + consultas
- **Custo estimado:** ~$60-100/mês

**Alternativa mais barata para MVP:**
- Amazon Athena (consulta direto no S3): paga $5 por TB escaneado
- Com 100GB de dados comprimidos em Parquet: ~$0.50/consulta = muito barato para MVP!
- **Recomendação:** Comece com Athena, migre para Redshift quando tiver >1TB de dados.

---

### 4. ElasticSearch (OpenSearch Service) — Buscas Full-Text

Para o usuário pesquisar "Construtora XYZ" e encontrar todos os contratos.

- **Instância:** t3.small.search (1 node para MVP)
- **Armazenamento:** 20GB EBS
- **Custo:** ~$35-45/mês

**Alternativa gratuita para MVP:**
- PostgreSQL full-text search (extensão pg_trgm) no RDS t3.micro
- Custo: ~$15/mês — suficiente até ~500k registros

---

### 5. ElastiCache (Redis) — Cache

Armazena resultados de consultas frequentes para o app não bater no banco toda vez.

- **Instância:** cache.t3.micro (0.5GB RAM)
- **Uso:** Queries do dashboard, top 10 fornecedores, etc.
- **TTL configurado:** 15 minutos para dados do dia atual, 24h para histórico
- **Custo:** ~$12-18/mês

---

### 6. Lambda — Alertas e Webhooks

Funções serverless para:
- Enviar e-mail quando um portal fica offline
- Enviar alerta no Slack quando a coleta falha
- Processar webhooks de notificação em tempo real

- **Invocações:** ~10.000/mês
- **Custo:** praticamente gratuito (Lambda tem 1 milhão de chamadas gratuitas/mês)
- **Custo:** ~$1/mês

---

### 7. API Gateway

Gerencia o acesso à API pública do sistema.

- **Requests:** ~500.000/mês (fase inicial)
- **Custo:** $3.50 por 1 milhão de chamadas
- **Custo estimado:** ~$2-5/mês

---

### 8. CloudWatch — Monitoramento

Métricas, logs e alertas de toda a infraestrutura.

- **Logs:** 10GB/mês
- **Métricas customizadas:** 20 métricas
- **Alarmes:** 10 alarmes configurados
- **Custo:** ~$5-8/mês

---

## Resumo de Custos por Fase

### Fase 1 — MVP (Federal + Capitais)
| Serviço          | Custo/mês |
|-----------------|-----------|
| EC2 (Airflow)    | $15       |
| EC2 Spot         | $10       |
| EC2 API          | $30       |
| S3 Data Lake     | $5        |
| Athena (DW)      | $10       |
| Redis Cache      | $15       |
| Lambda + Gateway | $5        |
| CloudWatch       | $5        |
| **TOTAL MVP**    | **~$95/mês** |

### Fase 2 — Capitais + 500 Municípios
| Serviço          | Custo/mês |
|-----------------|-----------|
| EC2 (todos)      | $80       |
| S3 Data Lake     | $15       |
| Redshift Server. | $80       |
| OpenSearch       | $40       |
| Redis            | $18       |
| Outros           | $20       |
| **TOTAL FASE 2** | **~$253/mês** |

### Fase 3 — Brasil Completo (5.570 municípios)
| Serviço          | Custo/mês |
|-----------------|-----------|
| EC2 (cluster)    | $200      |
| S3 Data Lake     | $50       |
| Redshift (8 nós) | $300      |
| OpenSearch       | $120      |
| Redis Cluster    | $80       |
| CDN (CloudFront) | $30       |
| Outros           | $70       |
| **TOTAL FASE 3** | **~$850/mês** |

---

## Estratégias de Redução de Custo

### 1. Savings Plans (compromisso de 1 ano = -30%)
```
EC2 Savings Plan 1 ano:
  Antes: $80/mês
  Depois: $56/mês
  Economia: $24/mês = $288/ano
```

### 2. Dados em Parquet (compressão = menos armazenamento)
```
JSON bruto:     100GB = $2.30/mês no S3
Parquet:         8GB = $0.18/mês no S3
Economia: 96% no armazenamento
```

### 3. Auto Scaling agressivo (paga só quando usa)
```
API Server com Auto Scaling:
  Horário noturno (0h-7h): 1 instância  = $10/mês
  Horário comercial (8h-22h): 3 instâncias = $30/mês
  vs. 3 instâncias 24/7: $90/mês
  Economia: 56%
```

### 4. Athena vs Redshift para MVP
```
Athena (pay-per-query):
  10.000 queries/mês × 50KB escaneado = $0.25/mês
  
Redshift Serverless:
  ~$80/mês fixo
  
Use Athena até ter 10M+ registros e >50k queries/mês
```

---

## Arquivo Terraform — Infraestrutura como Código

```hcl
# main.tf — Deploy automatizado da infraestrutura AWS
# Como usar:
#   1. Instale o Terraform: https://terraform.io
#   2. Configure suas credenciais AWS: aws configure
#   3. Execute: terraform init && terraform apply

terraform {
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.0" }
  }
}

provider "aws" {
  region = "sa-east-1"  # São Paulo — menor latência para o Brasil
}

# S3 — Data Lake
resource "aws_s3_bucket" "data_lake_raw" {
  bucket = "transparencia-br-raw-${random_id.suffix.hex}"
  
  tags = {
    Projeto     = "transparencia-br"
    Ambiente    = "producao"
    Fase        = "mvp"
  }
}

# Lifecycle: move dados antigos para camadas mais baratas
resource "aws_s3_bucket_lifecycle_configuration" "data_lake_lifecycle" {
  bucket = aws_s3_bucket.data_lake_raw.id

  rule {
    id     = "mover-para-ia-30-dias"
    status = "Enabled"
    
    transition {
      days          = 30
      storage_class = "STANDARD_IA"  # 46% mais barato que Standard
    }
    
    transition {
      days          = 365
      storage_class = "GLACIER_IR"   # 68% mais barato que Standard
    }
  }
}

# EC2 — Airflow Scheduler
resource "aws_instance" "airflow" {
  ami           = "ami-0c55b159cbfafe1f0"  # Amazon Linux 2
  instance_type = "t3.small"
  
  user_data = <<-EOF
    #!/bin/bash
    pip install apache-airflow
    airflow db init
    airflow scheduler &
    airflow webserver --port 8080 &
  EOF
  
  tags = { Name = "airflow-scheduler" }
}

# ElastiCache — Redis
resource "aws_elasticache_cluster" "redis" {
  cluster_id      = "transparencia-cache"
  engine          = "redis"
  node_type       = "cache.t3.micro"
  num_cache_nodes = 1
  port            = 6379
}

# Redshift Serverless
resource "aws_redshiftserverless_workgroup" "dw" {
  workgroup_name = "transparencia-dw"
  namespace_name = aws_redshiftserverless_namespace.dw.namespace_name
  base_capacity  = 8  # RPUs mínimas — escala automaticamente
}
```

---

## Checklist de Deploy (passo a passo para iniciantes)

```
□ 1. Criar conta AWS (Free Tier cobre 12 meses de serviços básicos)
□ 2. Instalar AWS CLI: pip install awscli && aws configure
□ 3. Instalar Terraform: https://developer.hashicorp.com/terraform/install
□ 4. Clonar este repositório
□ 5. cd infrastructure/terraform && terraform init
□ 6. terraform plan (mostra o que vai ser criado)
□ 7. terraform apply (cria a infraestrutura — ~10 minutos)
□ 8. Copiar scraper_betha.py para EC2 Airflow
□ 9. Copiar pipeline_airflow.py para a pasta dags/ do Airflow
□ 10. Acessar http://SEU-EC2-IP:8080 → ativar as DAGs
□ 11. Configurar Airflow Variables: chave_api_federal e slack_webhook_url
□ 12. Executar pipeline manualmente para testar
□ 13. Verificar dados chegando no S3
□ 14. Executar dbt run para processar e publicar dados
```
