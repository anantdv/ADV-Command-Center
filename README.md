# ADV Command Center

Enterprise React and FastAPI command center for permission-aware ERPNext/Frappe access, Tinni chat, dashboards, generated files, controlled draft CRUD, and privacy-gated Vertex Gemini intent extraction.

The Communications workspace adds a permission-aware business inbox, sent mail, threads, templates, document linking, explicit reply/forward actions, AI draft previews, and email-to-Task/Issue/Lead conversion on top of Frappe's standard Communication and email queue.

The Frappe companion app is maintained separately at [`anantdv/ai_command_center`](https://github.com/anantdv/ai_command_center) and is intentionally excluded from this repository.

## Local development

```bash
npm install
cd backend && python3.12 -m venv .venv && .venv/bin/pip install -r requirements.txt && cd ..
cp backend/.env.example backend/.env
npm run dev
```

- Frontend: `http://localhost:5173`
- FastAPI: `http://localhost:8000`
- OpenAPI: `http://localhost:8000/docs`

Configure `backend/.env` for the ERPNext site. Keep `USE_MOCK_DATA=false` for live integration. Vertex Gemini is optional and restricted to structured intent extraction; ERPNext records and report rows are not sent to external models.

See [backend/README.md](backend/README.md) for API configuration, security controls, deployment notes, and manual tests.

## Production build

```bash
npm ci
npm run build
```

Serve `dist/` through Nginx and run FastAPI from its dedicated virtual environment through systemd. Do not run the backend inside the Frappe Bench Python environment.

## Module workspace manual checks

The module pages are ERP workspaces only; Tinni chat lives in the Command Center.

```text
/modules/selling
/modules/selling/doctype/Customer
/modules/selling/doctype/Sales%20Invoice
/command-center?module=Selling
```

Expected behavior:

- `/modules/selling` has no bottom chat and no overlapping fixed chat area.
- “Ask AI” routes to `/command-center?module=Selling`.
- KPI/report/quick actions route to Command Center with `module`, `prompt`, and `autoRun`.
- DocType cards open list views with search, pagination, and clickable rows.
- Row click opens a permission-aware record detail drawer using the global ERPNext document detail API.
- Command Center “Pin” can target Overview or an accessible module; module-targeted pins appear on that module dashboard and are not shown on Overview.
