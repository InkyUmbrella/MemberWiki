from datetime import datetime, timezone

from fastapi import APIRouter

from app.core.config import settings

router = APIRouter(prefix=settings.api_v1_prefix)


@router.get("/health", tags=["System"])
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
from fastapi import APIRouter

from app.api.v1 import auth, profiles, reviews, search, uploads, users

router = APIRouter()
router.include_router(auth.router, prefix="/auth", tags=["Auth"])
router.include_router(users.router, prefix="/users", tags=["Users"])
router.include_router(profiles.router, prefix="/profiles", tags=["Profiles"])
router.include_router(reviews.router, prefix="/reviews", tags=["Reviews"])
router.include_router(search.router, prefix="/search", tags=["Search"])
router.include_router(uploads.router, prefix="/uploads", tags=["Uploads"])
