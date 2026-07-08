from fastapi import APIRouter

from app.api import analytics, auth, chat, communications, dashboard, debug, document_intake, erpnext, knowledge, library, modules, reports, support, training, workflow

api_router = APIRouter()
for router in (auth.router, dashboard.router, chat.router, communications.router, modules.router, library.router, training.router, support.router, knowledge.router, reports.router, document_intake.router, workflow.router, analytics.router, erpnext.router, debug.router):
    api_router.include_router(router)
