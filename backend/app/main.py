from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.config import settings
from app.core.exceptions import AppError
from app.db.base import Base
from app.db.session import engine
from app.logging_config import configure_logging
from app.schemas.errors import api_error

configure_logging()
logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings.validate_llm_runtime()
    settings.validate_rag_runtime()
    Base.metadata.create_all(bind=engine)
    logger.info("document_intake_routes_registered", prefix=f"{settings.api_prefix}/document-intake")
    yield


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan, docs_url="/docs", redoc_url="/redoc")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router, prefix=settings.api_prefix)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "app": settings.app_name, "mockMode": settings.use_mock_data}


@app.exception_handler(AppError)
async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
    code = str(exc.details.get("code") or "app_error")
    return JSONResponse(status_code=exc.status_code, content=api_error(code, exc.message, exc.message, include_debug=settings.app_env == "development", details=exc.details))


@app.exception_handler(HTTPException)
async def http_error_handler(_: Request, exc: HTTPException) -> JSONResponse:
    message = str(exc.detail)
    return JSONResponse(status_code=exc.status_code, content=api_error("http_error", message, message, include_debug=settings.app_env == "development"))


@app.exception_handler(RequestValidationError)
async def validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    errors = [{key: value for key, value in item.items() if key != "ctx"} for item in exc.errors()]
    return JSONResponse(status_code=422, content=api_error("validation_error", "Request validation failed", str(errors), include_debug=settings.app_env == "development", details={"errors": errors}))


@app.exception_handler(Exception)
async def unexpected_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("unhandled_backend_error", path=request.url.path, error_type=type(exc).__name__)
    return JSONResponse(
        status_code=500,
        content=api_error("internal_server_error", "The server could not complete this request.", str(exc), include_debug=settings.app_env == "development"),
    )
