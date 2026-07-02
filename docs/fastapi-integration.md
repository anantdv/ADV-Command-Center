# FastAPI frontend integration contract

## Adapter selection

Every feature service chooses its transport internally using `env.useMockApi`. Pages only call hooks and never import fixtures.

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_USE_MOCK_API=false
VITE_ERP_SITE_URL=https://erp.anantdv.com
VITE_APP_NAME=ERP AI Command Center
```

`npm run dev` starts FastAPI on port 8000 and Vite on port 5173 (or the next available port). The API client prefixes every path with `VITE_API_BASE_URL`, sends JSON, includes the HTTP-only Frappe session cookie, and converts failures into `ApiClientError`.

## Expected FastAPI endpoints

### Authentication and dashboard

- `GET /api/auth/me`
- `POST /api/auth/login`
- `POST /api/auth/logout`
- `GET /api/dashboard/overview`
- `GET /api/dashboard/widgets`
- `POST /api/dashboard/widgets`

### Chat

- `GET /api/chat/conversations`
- `POST /api/chat/conversations`
- `GET /api/chat/conversations/{id}/messages`
- `POST /api/chat/message`
- `POST /api/chat/actions/{id}/confirm`
- `POST /api/chat/actions/{id}/cancel`
- `GET /api/chat/seed` (temporary prototype visualization data)

`streamChatMessage()` currently exposes an async generator compatibility layer. Replace its internals with Server-Sent Events or WebSocket transport without changing page components.

### ERP modules and assets

- `GET /api/modules`
- `GET /api/modules/{moduleName}`
- `GET /api/modules/{moduleName}/records`
- `GET /api/modules/{moduleName}/reports`
- `GET /api/library/files`
- `POST /api/library/files`
- `DELETE /api/library/files/{id}`

### Training and support

- `GET /api/training/courses`
- `GET /api/training/results`
- `POST /api/training/assessments/{id}/submit`
- `GET /api/support/tickets`
- `POST /api/support/tickets`
- `POST /api/support/ai-help`

### ERPNext gateway

- `GET /api/erpnext/current-user-context`
- `GET /api/erpnext/allowed-doctypes`
- `POST /api/erpnext/doctype-schema`
- `POST /api/erpnext/list-records`
- `POST /api/erpnext/get-record`
- `POST /api/erpnext/create-record`
- `POST /api/erpnext/update-record`

## Response and permission rules

Authoritative request/response models are in `src/types/`. API errors should use FastAPI's standard `{ "detail": "..." }` shape. Domain responses may include `permissions: PermissionMeta`; restricted UI actions are disabled or hidden by the receiving components.

The browser never reads the Frappe session ID. FastAPI should validate the HTTP-only cookie and return `401` when it is missing or expired.
