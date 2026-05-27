from pydantic import BaseModel, Field

from app.models.enums import VerificationChannel, VerificationPurpose
from app.schemas.user import UserResponse


class RegisterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=50)
    email: str | None = None
    phone: str | None = None
    password: str = Field(min_length=8, max_length=72)
    code: str | None = None


class LoginRequest(BaseModel):
    account: str
    password: str = Field(min_length=8, max_length=72)


class SendCodeRequest(BaseModel):
    channel: VerificationChannel
    target: str
    purpose: VerificationPurpose


class VerifyCodeRequest(BaseModel):
    channel: VerificationChannel
    target: str
    code: str = Field(min_length=4, max_length=8)
    purpose: VerificationPurpose


class AuthTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int = 3600
    user: UserResponse
