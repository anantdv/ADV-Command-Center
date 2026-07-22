from fastapi import APIRouter

from app.api import analytics, auth, chat, command_center, communications, dashboard, debug, document_intake, erpnext, knowledge, library, modules, notifications, report_composer, reports, suggestions, support, training, workflow

api_router = APIRouter()
for router in (auth.router, dashboard.router, chat.router, command_center.router, communications.router, modules.router, notifications.router, library.router, training.router, support.router, knowledge.router, reports.router, report_composer.router, suggestions.router, document_intake.router, workflow.router, analytics.router, erpnext.router, debug.router):
    api_router.include_router(router)
