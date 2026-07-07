from fastapi import APIRouter

from app.api import auth, chat, communications, dashboard, debug, document_intake, erpnext, knowledge, library, modules, reports, support, training

api_router = APIRouter()
for router in (auth.router, dashboard.router, chat.router, communications.router, modules.router, library.router, training.router, support.router, knowledge.router, reports.router, document_intake.router, erpnext.router, debug.router):
    api_router.include_router(router)
