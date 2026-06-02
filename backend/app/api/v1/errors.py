from fastapi import HTTPException

from app.core.request_id import get_request_id
from app.core.result import Result

STATUS_MAP: dict[str, int] = {
    "UNAUTHORIZED": 401,
    "FORBIDDEN": 403,
    "NOT_FOUND": 404,
    "CONFLICT": 409,
    "VALIDATION_ERROR": 400,
}


def raise_for_result(result: Result) -> None:
    if not result.ok:
        raise HTTPException(
            status_code=STATUS_MAP.get(result.code or "", 500),
            detail={
                "code": result.code,
                "message": result.error,
                "request_id": get_request_id(),
            },
        )


__all__ = ["raise_for_result"]
