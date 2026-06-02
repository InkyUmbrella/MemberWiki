from fastapi import APIRouter, Depends, HTTPException
from fastapi import Request as FastAPIRequest
from sqlalchemy.orm import Session

from app.api.v1.errors import raise_for_result
from app.core.limiter import limiter
from app.core.log import get_logger
from app.db.session import get_db
from app.models.enums import VerificationChannel
from app.schemas.auth import (
    AuthTokenResponse,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    SendCodeRequest,
    VerifyCodeRequest,
)
from app.services import auth_service
from app.services.email_service import send_verification_code
from app.services.time import utcnow
from app.services.verification_service import generate_code, persist_code, verify_and_consume

log = get_logger(__name__)
router = APIRouter()


@router.post("/register", response_model=AuthTokenResponse, status_code=201)
@limiter.limit("10/minute")
def register(request: FastAPIRequest, payload: RegisterRequest, db: Session = Depends(get_db)) -> AuthTokenResponse:
    log.info(f"register: email={payload.email}")
    result = auth_service.register_user(
        db,
        name=payload.name,
        email=payload.email,
        phone=payload.phone,
        password=payload.password,
    )
    raise_for_result(result)
    db.commit()
    return result.unwrap()


@router.post("/login", response_model=AuthTokenResponse)
@limiter.limit("10/minute")
def login(request: FastAPIRequest, payload: LoginRequest, db: Session = Depends(get_db)) -> AuthTokenResponse:
    log.info(f"login: account={payload.account}")
    result = auth_service.login_user(db, account=payload.account, password=payload.password)
    raise_for_result(result)
    db.commit()
    return result.unwrap()


@router.post("/send-code", status_code=202)
def send_code(request: FastAPIRequest, payload: SendCodeRequest, db: Session = Depends(get_db)) -> dict[str, str]:
    if payload.channel != VerificationChannel.EMAIL:
        raise HTTPException(status_code=501, detail="only email verification is supported")
    log.info(f"send_code: channel={payload.channel.value} target={payload.target}")
    code = generate_code()
    try:
        send_result = send_verification_code(payload.target, code)
        if not send_result.ok:
            log.warn(f"send_code: failed to send to {payload.target}: {send_result.error}")
    except Exception as exc:
        log.warn(f"send_code: failed to send to {payload.target}: {exc}")
    persist_code(
        db,
        channel=payload.channel.value,
        target=payload.target,
        purpose=payload.purpose.value,
        code=code,
        ip=request.client.host if request.client else None,
        ua=request.headers.get("user-agent"),
    )
    db.commit()
    return {"message": "code sent", "timestamp": utcnow().isoformat()}


@router.post("/verify-code")
def verify_code(request: FastAPIRequest, payload: VerifyCodeRequest, db: Session = Depends(get_db)) -> dict[str, str]:
    if payload.channel != VerificationChannel.EMAIL:
        raise HTTPException(status_code=501, detail="only email verification is supported")
    log.info(f"verify_code: target={payload.target}")
    result = verify_and_consume(
        db,
        target=payload.target,
        purpose=payload.purpose.value,
        code=payload.code,
    )
    raise_for_result(result)
    db.commit()
    return {"status": "verified", "target": payload.target, "purpose": payload.purpose.value}


@router.post("/refresh", response_model=AuthTokenResponse)
def refresh(request: FastAPIRequest, payload: RefreshRequest, db: Session = Depends(get_db)) -> AuthTokenResponse:
    log.info("refresh token")
    result = auth_service.refresh_tokens(db, refresh_token=payload.refresh_token)
    raise_for_result(result)
    db.commit()
    return result.unwrap()
