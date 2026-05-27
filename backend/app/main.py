from datetime import datetime, timezone

from fastapi import APIRouter, FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.v1.router import router as api_v1_router
from app.core.config import settings
from app.services.errors import ServiceError

app = FastAPI(title="MemberWiki API", version="0.1.0")
api_router = APIRouter(prefix=settings.api_v1_prefix)


@app.exception_handler(ServiceError)
def handle_service_error(_: Request, exc: ServiceError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": str(exc)}},
    )


@api_router.get("/health", tags=["System"])
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }


api_router.include_router(api_v1_router)
app.include_router(api_router)
