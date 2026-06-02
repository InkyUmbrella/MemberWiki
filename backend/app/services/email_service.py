import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.error_codes import AuthErrors
from app.core.log import get_logger
from app.core.result import Result

log = get_logger(__name__)


def send_verification_code(to_email: str, code: str) -> Result[None]:
    with log.time(f"send_verification_code: to={to_email} {{elapsed}}"):
        from app.core.config import settings

        if not settings.smtp_host:
            return Result.failure(AuthErrors.SMTP_NOT_CONFIGURED)
        msg = MIMEMultipart("alternative")
        msg["From"] = settings.smtp_from
        msg["To"] = to_email
        msg["Subject"] = "MemberWiki 验证码"

        msg.attach(
            MIMEText(
                f"您好，您的 MemberWiki 验证码是：\n\n    {code}\n\n"
                "该验证码 10 分钟内有效，请勿透露给他人。",
                "plain",
                "utf-8",
            )
        )
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as server:
            server.starttls()
            if settings.smtp_username and settings.smtp_password:
                server.login(settings.smtp_username, settings.smtp_password)
            server.send_message(msg)
        return Result.success(None)
