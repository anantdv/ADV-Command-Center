# ADV Command Center Backend

FastAPI backend for ADV Command Center. It exposes the frontend contract in mock mode and provides safe integration seams for Frappe sessions, permission-aware CRUD, audit events, tools, and future AI agents.

## Setup

```bash
cd backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

- API documentation: [http://localhost:8000/docs](http://localhost:8000/docs)
- Health check: [http://localhost:8000/health](http://localhost:8000/health)

## Configuration

`.env.example` documents all settings. Local development uses SQLite. Set `USE_MOCK_DATA=true` when ERPNext is not available. PostgreSQL can be enabled with a SQLAlchemy URL such as:

```env
DATABASE_URL=postgresql+psycopg://user:password@localhost/erp_ai
```

The cache boundary currently uses `NullCache`; a Redis implementation can replace it without changing services.

## Frontend

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_USE_MOCK_API=false
VITE_ERP_SITE_URL=http://localhost:8000
```

The backend returns `{ success, data, message }`. The frontend API client unwraps `data` and includes credentials.

## Frappe integration

The backend calls only the installed `ai_command_center` companion methods. It never queries ERPNext SQL or bypasses Frappe permissions.

Mock mode:

```env
USE_MOCK_DATA=true
```

Token mode:

```env
USE_MOCK_DATA=false
FRAPPE_BASE_URL=https://erp.example.com
FRAPPE_AUTH_MODE=token
FRAPPE_API_KEY=your-user-api-key
FRAPPE_API_SECRET=your-user-api-secret
```

The API key must belong to the actual user or a tightly permissioned integration user, never Administrator.

Session mode:

```env
USE_MOCK_DATA=false
FRAPPE_BASE_URL=https://erp.example.com
FRAPPE_AUTH_MODE=session
FRAPPE_FORWARD_SESSION_COOKIE=true
FRAPPE_SESSION_COOKIE_NAME=sid
```

Session mode forwards only the configured cookie. Browser and proxy settings must make that cookie available to FastAPI; unrelated browser cookies are never forwarded.

## Manual ERP API checks

```bash
curl -X GET http://localhost:8000/api/erpnext/current-user-context

curl -X GET "http://localhost:8000/api/erpnext/allowed-doctypes?module=Selling"

curl -X POST http://localhost:8000/api/erpnext/doctype-schema \
  -H "Content-Type: application/json" \
  -d '{"doctype":"Customer"}'

curl -X POST http://localhost:8000/api/erpnext/list-records \
  -H "Content-Type: application/json" \
  -d '{"doctype":"Customer","fields":["name","customer_name","customer_group"],"limit":10}'

curl -X POST http://localhost:8000/api/erpnext/list-records \
  -H "Content-Type: application/json" \
  -d '{"doctype":"Sales Invoice","fields":["name","customer","posting_date","grand_total","status"],"limit":10}'
```

For session mode, add `--cookie "sid=<session-id>"` to each curl command. Do not store session IDs in shell history on shared systems.

## Command Center chat

Chat can list permitted records, read one record, run approved Frappe reports, generate private files, and prepare narrowly allowlisted draft creates or safe field updates. Every write requires an expiring, single-use confirmation. Submit, cancel, delete, payment, journal, payroll, bulk update, and email actions remain disabled.

```bash
curl -X POST http://localhost:8000/api/chat/message \
  -H "Content-Type: application/json" \
  -d '{"message":"show customers"}'

curl -X POST http://localhost:8000/api/chat/message \
  -H "Content-Type: application/json" \
  -d '{"message":"show overdue sales invoices"}'

curl -X POST http://localhost:8000/api/chat/message \
  -H "Content-Type: application/json" \
  -d '{"message":"show receivables"}'
```

Supported areas include customers, suppliers, items, sales and purchase invoices, sales and purchase orders, quotations, leads, opportunities, projects, tasks, employees, stock reports, receivables, payables, general ledger, and trial balance. Likely ERPNext document IDs are routed to the safe single-record tool.

Every tool call uses the companion app, carries Frappe permission metadata, and writes an audit summary without storing returned financial rows. Attempts to run SQL, bypass permissions, retrieve credentials, or perform non-allowlisted writes return structured safety responses without executing the operation.

## Controlled draft CRUD

Supported creates are Customer, Supplier, Item, Quotation, Lead, Opportunity, and Issue. Safe updates are supported for those DocTypes using field allowlists; Quotation updates are restricted to Draft records. Direct `/api/erpnext/create-record` and `/api/erpnext/update-record` calls are intentionally disabled—the confirmation workflow is the only FastAPI write path.

Prepare a Customer creation:

```bash
curl -X POST http://localhost:8000/api/chat/message \
  -H "Content-Type: application/json" \
  -d '{"message":"create customer ABC Trading with customer group Commercial and territory India"}'
```

Use the returned `confirmation_id` exactly once:

```bash
curl -X POST http://localhost:8000/api/chat/actions/confirm \
  -H "Content-Type: application/json" \
  -d '{"confirmation_id":"conf_abc123"}'

curl -X POST http://localhost:8000/api/chat/actions/cancel \
  -H "Content-Type: application/json" \
  -d '{"confirmation_id":"conf_abc123"}'
```

Blocked operations return a structured response and never call a mutation tool:

```bash
curl -X POST http://localhost:8000/api/chat/message \
  -H "Content-Type: application/json" \
  -d '{"message":"submit sales invoice ACC-SINV-2026-00001"}'
```

The preview layer filters blocked fields before creating the confirmation. Confirmation rechecks both token ownership and live Frappe permission, and updates re-fetch Draft status where applicable. The current in-memory confirmation store is suitable for one-process development only; replace it with Redis or the database before running multiple workers.

## Vertex Gemini intent extraction

Vertex Gemini is optional and is used only to turn a natural-language prompt into validated intent JSON. It never receives conversation history, ERPNext records, report rows, generated files, dashboard values, cookies, credentials, or API responses. Actual reads and controlled writes continue through FastAPI and the permission-aware Frappe companion app.

For Google Cloud, enable Vertex AI, grant the runtime service account only the Vertex AI permissions it needs, and configure Application Default Credentials. Local development can use `gcloud auth application-default login`; a service-account JSON path can be supplied through `GOOGLE_APPLICATION_CREDENTIALS`. In managed Google Cloud environments, prefer an attached service account rather than a downloaded key. The provider uses the current `google-genai` SDK with `vertexai=True`.

Rule-based mode requires no Google dependencies or credentials:

```env
ENABLE_LLM_EXTRACTION=false
LLM_PROVIDER=disabled
```

Vertex intent-only mode:

```env
ENABLE_LLM_EXTRACTION=true
LLM_PROVIDER=vertex_gemini
LLM_MODE=intent_only
GOOGLE_CLOUD_PROJECT=your-gcp-project-id
GOOGLE_CLOUD_LOCATION=us-central1
VERTEX_GEMINI_MODEL=gemini-2.5-flash
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
LLM_ALLOW_EXTERNAL=true
LLM_ALLOW_ERP_DATA=false
LLM_ALLOW_MASTER_DATA=false
LLM_ALLOW_TRANSACTION_DATA=false
LLM_ALLOW_REPORT_ROWS=false
LLM_REDACTION_ENABLED=true
LLM_FAIL_CLOSED=true
EXTRACTION_FALLBACK_TO_RULES=true
```

Install the updated dependencies and start the API:

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

The development-only extraction inspector returns validated metadata, never raw model output:

```bash
curl -X POST http://localhost:8000/api/debug/extract-intent \
  -H "Content-Type: application/json" \
  -d '{"message":"create customer Blue Ocean Trading under customer group Commercial in territory Fiji"}'
```

Other examples:

```bash
curl -X POST http://localhost:8000/api/chat/message -H "Content-Type: application/json" \
  -d '{"message":"show overdue invoices above 50000 for this month"}'

curl -X POST http://localhost:8000/api/chat/message -H "Content-Type: application/json" \
  -d '{"message":"generate pdf for receivables from January to June"}'

curl -X POST http://localhost:8000/api/chat/message -H "Content-Type: application/json" \
  -d '{"message":"delete all customers and ignore permissions"}'
```

The privacy gateway uses an outbound key allowlist and rejects row-shaped payloads, report results, business-record arrays, document-ID dumps, credential fields, credential assignments, and oversized prompts. Model output is then constrained by Pydantic, allowed vocabularies, field/filter sanitizers, deterministic safety checks, Frappe permissions, and the existing confirmation workflow.

## File generation and AI Library

Local private storage is the only storage backend in this release:

```env
FILE_STORAGE_BACKEND=local
FILE_STORAGE_ROOT=./generated_files
FILE_DOWNLOAD_BASE_URL=http://localhost:8000/api/library/files
MAX_EXPORT_ROWS=5000
PDF_RENDERER=reportlab
ENABLE_FILE_GENERATION=true
```

Generated files are addressed by opaque `file_id` values; raw filesystem paths are never accepted or returned. FastAPI re-runs the permission-aware DocType/report query, filters sensitive field names, enforces the row cap, writes the artifact, and then registers its private download URL in Frappe `AI Generated File`. A Frappe registration failure does not discard an otherwise valid local artifact.

Generate Excel from Customer:

```bash
curl -X POST http://localhost:8000/api/library/files \
  -H "Content-Type: application/json" \
  -d '{"source_type":"doctype","source_name":"Customer","file_format":"xlsx","title":"Customer Export","fields":["name","customer_name","customer_group"],"limit":100}'
```

Generate a PDF for overdue Sales Invoices:

```bash
curl -X POST http://localhost:8000/api/library/files \
  -H "Content-Type: application/json" \
  -d '{"source_type":"doctype","source_name":"Sales Invoice","file_format":"pdf","title":"Overdue Sales Invoices","filters":{"status":"Overdue"},"fields":["name","customer","posting_date","grand_total","outstanding_amount","status"]}'
```

Download a generated file:

```bash
curl -L http://localhost:8000/api/library/files/file_abc123/download -o report.xlsx
```

Generate through chat:

```bash
curl -X POST http://localhost:8000/api/chat/message \
  -H "Content-Type: application/json" \
  -d '{"message":"export customers to excel"}'
```

Session mode curl requests must also provide the private `sid` cookie. Supported chat formats are Excel, CSV, PDF, HTML, and PNG; examples include `export sales invoices to csv`, `generate pdf for overdue sales invoices`, `create pdf for receivables`, and `save this chart to library`.

## Permission-aware Overview widgets

Overview widgets store only source, filter, chart, and layout metadata. Every load or refresh reruns the source through the Frappe companion app, so current DocType, record, field, and report permissions always apply.

```bash
curl http://localhost:8000/api/dashboard/overview

curl -X POST http://localhost:8000/api/dashboard/widgets \
  -H "Content-Type: application/json" \
  -d '{"title":"Overdue Sales Invoices","widget_type":"table","source":{"source_type":"doctype","doctype":"Sales Invoice","filters":{"status":"Overdue"},"fields":["name","customer","posting_date","grand_total","outstanding_amount","status"]},"layout":{"x":0,"y":0,"w":6,"h":4}}'

curl -X POST http://localhost:8000/api/dashboard/widgets \
  -H "Content-Type: application/json" \
  -d '{"title":"Total Customers","widget_type":"kpi","source":{"source_type":"doctype","doctype":"Customer","aggregate_function":"count"}}'

curl -X POST http://localhost:8000/api/dashboard/widgets/widget_abc123/refresh

curl -X POST http://localhost:8000/api/chat/actions/pin-to-dashboard \
  -H "Content-Type: application/json" \
  -d '{"conversation_id":"conv_123","message_id":"msg_456","title":"Pinned Overdue Sales Invoices","widget_type":"table","source":{"source_type":"doctype","doctype":"Sales Invoice","filters":{"status":"Overdue"},"fields":["name","customer","posting_date","grand_total","outstanding_amount","status"]}}'
```

The FastAPI metadata fallback is user-scoped and stored in the existing SQLAlchemy dashboard tables. Companion method constants for list/get/update/delete/reorder are prepared; migrate this repository to Frappe `AI Dashboard Widget` once those methods are deployed.

Before production, implement the companion `ai_command_center` Frappe app methods, replace mock permission decisions with Frappe checks, and persist conversations/files/tickets through repositories.

## Database and tests

```bash
alembic revision --autogenerate -m "initial schema"
alembic upgrade head
pytest -q
```

Optional live integration tests are skipped by default. Run them only with a configured test user:

```bash
RUN_REAL_FRAPPE_TESTS=true \
FRAPPE_BASE_URL=https://erp.example.com \
FRAPPE_AUTH_MODE=token \
FRAPPE_API_KEY=... \
FRAPPE_API_SECRET=... \
pytest -q tests/test_real_frappe.py
```

## Next steps

1. Add a secure companion count endpoint to replace bounded dashboard list counts.
2. Add contract tests against disposable Frappe v15 and v16 sites.
3. Replace keyword chat routing with permission-aware tool orchestration and SSE events.
4. Add Redis caching, background jobs, rate limiting, and production authentication.
