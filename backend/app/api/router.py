from fastapi import APIRouter

from app.api import auth, chat, communications, dashboard, debug, erpnext, knowledge, library, modules, support, training

api_router = APIRouter()
for router in (auth.router, dashboard.router, chat.router, communications.router, modules.router, library.router, training.router, support.router, knowledge.router, erpnext.router, debug.router):
    api_router.include_router(router)
