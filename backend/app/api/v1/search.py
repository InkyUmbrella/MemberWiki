from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.v1.errors import raise_for_result
from app.core.log import get_logger
from app.db.session import get_db
from app.schemas.common import PaginatedResponse
from app.schemas.profile import SearchResultItem
from app.services.search_service import search_members

log = get_logger(__name__)
router = APIRouter()


@router.get("/members", response_model=PaginatedResponse[SearchResultItem])
def search(
    keyword: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> PaginatedResponse[SearchResultItem]:
    log.info(f"search: keyword={keyword} page={page}")
    result = search_members(db, keyword=keyword, limit=page_size)
    raise_for_result(result)
    items, total = result.unwrap()
    return PaginatedResponse(items=items, page=page, page_size=page_size, total=total)
