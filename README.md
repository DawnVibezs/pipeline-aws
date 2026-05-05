# 🚀 Serverless Data Processing Pipeline

[🇺🇸 Read in English](#the-business-problem) | [🇧🇷 Ler em Português](#o-problema-de-negocio)

[![CI](https://github.com/DawnVibez/pipeline-aws/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/DawnVibez/pipeline-aws/actions)
![Python](https://img.shields.io/badge/Python-3.14-blue?logo=python&logoColor=white)
![AWS Lambda](https://img.shields.io/badge/AWS-Lambda-FF9900?logo=awslambda&logoColor=white)
![AWS S3](https://img.shields.io/badge/AWS-S3-569A31?logo=amazons3&logoColor=white)
![DynamoDB](https://img.shields.io/badge/AWS-DynamoDB-4053D6?logo=amazondynamodb&logoColor=white)
![Tests](https://img.shields.io/badge/tests-47%20passing-brightgreen?logo=pytest&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-green)

> Automated, observable, and fault-tolerant data ingestion pipeline — built on AWS serverless architecture.

---

## The Business Problem

Every data-driven company faces the same challenge: **receiving files from different sources, in different formats, and needing to process them reliably, automatically, and with full traceability.**

Manual processing creates bottlenecks. Brittle scripts create blind spots. This pipeline solves both.

---

## What It Does

When a file lands in S3, the system **automatically**:

1. Detects the format (CSV or JSON)
2. Validates every record against a defined schema
3. Transforms and normalizes the data
4. Routes valid records to a processed store and invalid ones to a quarantine bucket — with a full error report
5. Persists the job result in DynamoDB for auditability
6. Exposes the result through a secure REST API
7. Publishes real-time metrics to CloudWatch — with alarms and a live dashboard

No servers to manage. No manual intervention. Full observability from day one.

---

## Architecture

```
┌─────────────┐     PUT file     ┌──────────────┐    S3 trigger     ┌─────────────────────┐
│   Client    │ ───────────────► │  S3: raw/    │ ───────────────►  │   λ Lambda          │
└─────────────┘                  └──────────────┘                   │   (Python)          │
                                                                    │                     │
                                                                    │  • Detect format    │
                                                                    │  • Validate schema  │
                                                                    │  • Transform data   │
                                                                    └──────────┬──────────┘
                                                                               │
                                              ┌────────────────────────────────┼──────────────────┐
                                              ▼                                ▼                  ▼
                                   ┌──────────────────┐            ┌─────────────────┐  ┌─────────────────┐
                                   │  S3: processed/  │            │  S3: errors/    │  │   CloudWatch    │
                                   └────────┬─────────┘            └─────────────────┘  │  Logs + Metrics │
                                            │                                           └─────────────────┘
                                            ▼
                                   ┌─────────────────┐
                                   │    DynamoDB     │
                                   │  (job results)  │
                                   └────────┬────────┘
                                            │
                                            ▼
                                   ┌─────────────────┐         ┌─────────────┐
                                   │  API Gateway    │ ◄────── │   Client    │
                                   │  + λ Lambda     │         └─────────────┘
                                   └─────────────────┘
```

---

## Tech Stack

| Layer | Technology | Why |
|---|---|---|
| Compute | AWS Lambda (Python 3.14) | Zero infrastructure overhead, pay-per-use |
| Storage | AWS S3 | Durable, scalable object storage with event triggers |
| Database | AWS DynamoDB | Sub-millisecond reads, serverless, built-in TTL |
| API | AWS API Gateway | Managed routing, throttling, and TLS out of the box |
| Observability | AWS CloudWatch | Metrics, alarms, and dashboards in one place |
| Auth | API Key + SHA-256 | Timing-attack-safe key validation |

---

## API Reference

Authentication: all endpoints require the `x-api-key` header.

### `GET /results/{job_id}`

Returns the processing result for a specific job.

**Response `200 OK`**
```json
{
  "success": true,
  "data": {
    "job_id": "550e8400-e29b-41d4-a716-446655440000",
    "source_file": "raw/customers_2024.csv",
    "status": "SUCCESS",
    "total_records": 500,
    "valid_records": 487,
    "error_count": 13,
    "output_key": "processed/550e8400.json",
    "started_at": "2024-11-01T14:32:00Z",
    "finished_at": "2024-11-01T14:32:03Z"
  },
  "meta": { "timestamp": "2024-11-01T14:33:00Z" }
}
```

### `GET /results?limit=20&status=FAILED`

Lists all jobs with cursor-based pagination and optional status filter.

| Param | Type | Description |
|---|---|---|
| `limit` | int | Items per page (default: 20, max: 100) |
| `status` | string | Filter by `SUCCESS` or `FAILED` |
| `last_evaluated` | string | Pagination cursor from previous response |

---

## Observability

The system publishes custom CloudWatch metrics under the `DataPipeline` namespace:

| Metric | Unit | Description |
|---|---|---|
| `JobSuccess` | Count | Successfully processed jobs |
| `JobFailure` | Count | Failed jobs (by error type) |
| `JobDurationMs` | Milliseconds | Processing time (p50 / p90 / p99) |
| `RecordsThroughput` | Count/Second | Records processed per second |
| `ValidationErrorRate` | Percent | Share of invalid records per job |
| `ApiLatencyMs` | Milliseconds | API response time (p95) |
| `UnauthorizedRequests` | Count | Failed auth attempts (security monitoring) |

**5 alarms** fire automatically via SNS email when thresholds are breached — including a spike detector for unauthorized access attempts.

---

## Project Structure

```
pipeline-aws/
├── src/
│   ├── handler.py        # Pipeline Lambda — entry point
│   ├── processor.py      # CSV and JSON parsing
│   ├── validator.py      # Schema validation + data normalization
│   ├── storage.py        # DynamoDB operations (save, get, list + pagination)
│   ├── utils.py          # Shared utilities
│   ├── api_handler.py    # API Lambda — entry point
│   ├── auth.py           # API Key authentication
│   ├── routes.py         # Request routing + input validation
│   ├── response.py       # Standardized response envelope
│   └── observability.py  # CloudWatch metrics publisher
├── infra/
│   └── cloudwatch_infra.py  # Alarms + Dashboard provisioning script
├── tests/
│   ├── test_pipeline.py     # 18 tests — parsing, validation, transformation
│   ├── test_api.py          # 17 tests — auth, routing, responses
│   └── test_observability.py # 12 tests — metrics, timers, fault tolerance
└── samples/
    ├── sample_valid.csv
    └── sample_valid.json
```

---

## Running the Tests

We highly recommend using a virtual environment (`venv`) to avoid version conflicts.

```bash
# 1. Create the virtual environment
python -m venv venv

# 2. Activate it
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the tests (From the src/ directory)
cd src
python -m unittest discover -s ../tests -v
```
---

## Environment Variables

| Variable | Description |
|---|---|
| `RAW_BUCKET` | S3 bucket for incoming files |
| `PROCESSED_BUCKET` | S3 bucket for processed output |
| `ERRORS_BUCKET` | S3 bucket for quarantined files |
| `DYNAMO_TABLE` | DynamoDB table name |
| `API_KEY_HASH` | SHA-256 hash of the API key |
| `METRICS_NAMESPACE` | CloudWatch namespace (default: `DataPipeline`) |
| `ENVIRONMENT` | Deployment environment (`production`, `staging`) |
| `ALERT_EMAIL` | Email address for CloudWatch alarm notifications |

To generate the `API_KEY_HASH`:
```bash
python3 -c "from src.auth import generate_key_hash; print(generate_key_hash('your-secret-key'))"
```

---

## What I Learned Building This

Designing this pipeline pushed me to think beyond "make it work" and toward "make it trustworthy." A few things that stuck with me:

- **Observability is not a feature — it's a requirement.** Metrics need to fail silently so they never take down the business logic they're watching.
- **Error handling is product design.** Routing invalid records to a quarantine bucket instead of dropping them means the data team can investigate and reprocess — no data is silently lost.
- **Security decisions have to be intentional.** Using `hmac.compare_digest` instead of `==` for key comparison isn't just a best practice — it's the difference between a system that's secure and one that only looks secure.

---

*Built with Python 3.14 · AWS Lambda · S3 · DynamoDB · API Gateway · CloudWatch*

---
---

# 🚀 Pipeline de Processamento de Dados Serverless

[EN](#the-business-problem) | **PT-BR**

> Pipeline de ingestão de dados automatizado, observável e tolerante a falhas — construído sobre arquitetura serverless na AWS.

---

## O Problema de Negocio

Todo negócio orientado a dados enfrenta o mesmo desafio: **receber arquivos de diferentes fontes, em formatos diferentes, e precisar processá-los de forma confiável, automática e com rastreabilidade completa.**

Processamento manual cria gargalos. Scripts frágeis criam pontos cegos. Este pipeline resolve os dois.

---

## O Que Ele Faz

Quando um arquivo chega no S3, o sistema **automaticamente**:

1. Detecta o formato (CSV ou JSON)
2. Valida cada registro contra um schema definido
3. Transforma e normaliza os dados
4. Encaminha registros válidos para o bucket processado e inválidos para quarentena — com relatório de erros completo
5. Persiste o resultado do job no DynamoDB para auditoria
6. Expõe o resultado por uma API REST segura
7. Publica métricas em tempo real no CloudWatch — com alarmes e dashboard ao vivo

Sem servidores para gerenciar. Sem intervenção manual. Observabilidade completa desde o primeiro dia.

---

## Decisões Técnicas

**Por que Lambda + S3 e não uma fila (SQS)?**
Para este volume e caso de uso, o trigger nativo do S3 é suficiente e elimina uma camada. Se o volume crescer ou o processamento precisar de retry com backoff, a migração para SQS é natural — a lógica do Lambda não muda.

**Por que DynamoDB e não RDS?**
Resultados de jobs são lidos por `job_id` — acesso por chave, sem joins. DynamoDB entrega isso com latência sub-milissegundo e zero gestão de conexões, que é um problema real em ambientes serverless.

**Por que paginação via cursor e não por offset?**
Offset (`LIMIT 20 OFFSET 100`) degenera em tabelas grandes porque o banco precisa contar e descartar registros. Cursor-based pagination lê exatamente o que vai ser retornado, independente do tamanho da tabela.

---

## Como Rodar os Testes

Recomendamos fortemente o uso de um ambiente virtual (`venv`) para evitar conflitos de dependências.

```bash
# 1. Crie o ambiente virtual
python -m venv venv

# 2. Ative o ambiente
# No Windows:
venv\Scripts\activate
# No Linux/macOS:
source venv/bin/activate

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Rode os testes (A partir da pasta src/)
cd src
python -m unittest discover -s ../tests -v
```
---

## Estrutura do Projeto

```text
pipeline-aws/
├── src/
│   ├── handler.py          # Lambda do pipeline — entry point
│   ├── processor.py        # Parse de CSV e JSON
│   ├── validator.py        # Validação de schema + normalização
│   ├── storage.py          # DynamoDB (save, get, list + paginação)
│   ├── utils.py            # Utilitários compartilhados
│   ├── api_handler.py      # Lambda da API — entry point
│   ├── auth.py             # Autenticação por API Key
│   ├── routes.py           # Roteamento + validação de input
│   ├── response.py         # Envelope de resposta padronizado
│   └── observability.py    # Publicador de métricas CloudWatch
├── infra/
│   └── cloudwatch_infra.py # Script de provisionamento — alarmes + dashboard
├── tests/
│   ├── test_pipeline.py       # 18 testes
│   ├── test_api.py            # 17 testes
│   └── test_observability.py  # 12 testes
└── samples/
    ├── sample_valid.csv
    └── sample_valid.json
```
---

*Construído com Python 3.14 · AWS Lambda · S3 · DynamoDB · API Gateway · CloudWatch*