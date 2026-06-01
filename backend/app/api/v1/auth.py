from fastapi import APIRouter, Depends, HTTPException
from fastapi import Request as FastAPIRequest
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.limiter import limiter
from app.models.enums import VerificationChannel
from app.schemas.auth import AuthTokenResponse, LoginRequest, RegisterRequest, SendCodeRequest, VerifyCodeRequest
from app.services import auth_service
from app.services.email_service import send_verification_code
from app.services.verification_service import generate_code, persist_code
from app.services.time import utcnow

router = APIRouter()


@router.post("/register", response_model=AuthTokenResponse, status_code=201)
@limiter.limit("10/minute")
def register(request: FastAPIRequest, payload: RegisterRequest, db: Session = Depends(get_db)) -> AuthTokenResponse:
    response = auth_service.register_user(
        db,
        name=payload.name,
        email=payload.email,
        phone=payload.phone,
        password=payload.password,
    )
    db.commit()
    return response


@router.post("/login", response_model=AuthTokenResponse)
@limiter.limit("10/minute")
def login(request: FastAPIRequest, payload: LoginRequest, db: Session = Depends(get_db)) -> AuthTokenResponse:
    response = auth_service.login_user(db, account=payload.account, password=payload.password)
    db.commit()
    return response


@router.post("/send-code", status_code=202)
def send_code(request: FastAPIRequest, payload: SendCodeRequest, db: Session = Depends(get_db)) -> dict[str, str]:
    if payload.channel != VerificationChannel.EMAIL:
        raise HTTPException(status_code=501, detail="only email verification is supported")
    code = generate_code()
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
    try:
        send_verification_code(payload.target, code)
    except RuntimeError:
        pass
    except Exception:
        pass
    return {"message": "code sent", "timestamp": utcnow().isoformat()}


@router.post("/verify-code", response_model=AuthTokenResponse)
def verify_code(payload: VerifyCodeRequest) -> AuthTokenResponse:
    # TODO(integration): verify code then issue AuthTokenResponse.
    raise HTTPException(status_code=501, detail="verification-code login is not wired yet")
