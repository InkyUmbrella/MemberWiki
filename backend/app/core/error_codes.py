class ErrorDef:
    __slots__ = ("message", "code")

    def __init__(self, message: str, code: str) -> None:
        self.message = message
        self.code = code


class AuthErrors:
    INVALID_CREDENTIALS = ErrorDef("invalid account or password", "UNAUTHORIZED")
    ACCOUNT_EXISTS = ErrorDef("account already exists", "CONFLICT")
    EMAIL_REQUIRED = ErrorDef("email is required", "VALIDATION_ERROR")
    EMAIL_OR_PHONE_REQUIRED = ErrorDef("email or phone is required", "VALIDATION_ERROR")
    INVALID_TOKEN = ErrorDef("invalid or expired access token", "UNAUTHORIZED")
    TOKEN_EXPIRED = ErrorDef("refresh token expired", "UNAUTHORIZED")
    TOKEN_REUSE = ErrorDef("token reuse detected — session revoked", "UNAUTHORIZED")
    USER_DISABLED = ErrorDef("account is disabled", "FORBIDDEN")
    ACCOUNT_NOT_FOUND_OR_DISABLED = ErrorDef("account not found or disabled", "UNAUTHORIZED")
    INVALID_CODE = ErrorDef("invalid or expired verification code", "UNAUTHORIZED")
    AUTH_HEADER_REQUIRED = ErrorDef("authorization header is required", "UNAUTHORIZED")
    USER_NOT_FOUND = ErrorDef("user not found", "UNAUTHORIZED")
    NOT_ACCESS_TOKEN = ErrorDef("not an access token", "UNAUTHORIZED")
    SMTP_NOT_CONFIGURED = ErrorDef("SMTP is not configured", "INTERNAL_ERROR")
    CODE_SEND_FAILED = ErrorDef("failed to send verification code", "INTERNAL_ERROR")


class ProfileErrors:
    NOT_FOUND = ErrorDef("profile not found", "NOT_FOUND")
    DRAFT_NOT_FOUND = ErrorDef("latest draft not found", "NOT_FOUND")
    CANNOT_EDIT_OTHERS = ErrorDef("cannot edit another user's profile", "FORBIDDEN")
    INVALID_PROOF_FILES = ErrorDef("invalid proof_file_ids", "VALIDATION_ERROR")


class ReviewErrors:
    NOT_FOUND = ErrorDef("review not found", "NOT_FOUND")
    NOT_PENDING = ErrorDef("review is not pending", "CONFLICT")
    ALREADY_PENDING = ErrorDef("profile already has a pending review", "CONFLICT")
    DRAFT_ALREADY_PENDING = ErrorDef("latest draft is already pending", "CONFLICT")
    NO_DRAFT_ID = ErrorDef("review has no draft_id", "VALIDATION_ERROR")
    ADMIN_ONLY = ErrorDef("only admin can approve reviews", "FORBIDDEN")
    ADMIN_ONLY_REJECT = ErrorDef("only admin can reject reviews", "FORBIDDEN")
    CANNOT_SUBMIT_OTHERS = ErrorDef("cannot submit another user's profile", "FORBIDDEN")
    DRAFT_OR_PROFILE_NOT_FOUND = ErrorDef("review draft or profile not found", "NOT_FOUND")


class UploadErrors:
    NOT_FOUND = ErrorDef("file not found", "NOT_FOUND")
    CANNOT_DELETE_OTHERS = ErrorDef("cannot delete another user's file", "FORBIDDEN")
    FILE_NAME_REQUIRED = ErrorDef("file_name is required", "VALIDATION_ERROR")
    FILE_PATH_REQUIRED = ErrorDef("file_path is required", "VALIDATION_ERROR")
    FILE_SIZE_NOT_POSITIVE = ErrorDef("file_size must be positive", "VALIDATION_ERROR")


__all__ = ["ErrorDef", "AuthErrors", "ProfileErrors", "ReviewErrors", "UploadErrors"]
