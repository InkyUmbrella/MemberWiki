from datetime import datetime, timezone

from fastapi import APIRouter, FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.v1.router import router as api_v1_router
from app.core.config import settings
from app.core.errors import register_exception_handlers
from app.core.limiter import limiter
from app.core.request_id import register_request_id_middleware
from app.services.errors import ServiceError


def handle_service_error(_: Request, exc: ServiceError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": str(exc)}},
    )


def health() -> dict[str, str]:
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }


def create_app() -> FastAPI:
    app = FastAPI(title="MemberWiki API", version="0.1.0")
    register_request_id_middleware(app)
    register_exception_handlers(app)
    app.add_exception_handler(ServiceError, handle_service_error)

    app.state.limiter = limiter
    app.add_exception_handler(429, _rate_limit_exceeded_handler)

    api_router = APIRouter(prefix=settings.api_v1_prefix)
    api_router.add_api_route("/health", health, methods=["GET"], tags=["System"])
    api_router.include_router(api_v1_router)
    app.include_router(api_router)
    return app


def _rate_limit_exceeded_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=429,
        content={"error": {"code": "RATE_LIMITED", "message": "too many requests"}},
    )


app = create_app()
