from fastapi import APIRouter

from app.api import analytics, auth, business_graph, chat, command_center, communications, dashboard, debug, document_intake, erpnext, knowledge, library, metadata, modules, notifications, report_composer, reports, suggestions, support, task_plans, training, workflow

api_router = APIRouter()
for router in (auth.router, dashboard.router, chat.router, command_center.router, communications.router, modules.router, notifications.router, library.router, training.router, support.router, task_plans.router, metadata.router, business_graph.router, knowledge.router, reports.router, report_composer.router, suggestions.router, document_intake.router, workflow.router, analytics.router, erpnext.router, debug.router):
    api_router.include_router(router)
