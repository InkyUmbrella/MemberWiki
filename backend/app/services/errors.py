from app.core.errors import AppError


class ServiceError(AppError):
    pass


class UnauthorizedError(ServiceError):
    def __init__(self, message: str = "unauthorized") -> None:
        super().__init__(code="UNAUTHORIZED", message=message, status_code=401)


class ConflictError(ServiceError):
    def __init__(self, message: str = "conflict") -> None:
        super().__init__(code="CONFLICT", message=message, status_code=409)


class NotFoundError(ServiceError):
    def __init__(self, message: str = "not found") -> None:
        super().__init__(code="NOT_FOUND", message=message, status_code=404)


class ForbiddenError(ServiceError):
    def __init__(self, message: str = "forbidden") -> None:
        super().__init__(code="FORBIDDEN", message=message, status_code=403)


class ValidationError(ServiceError):
    def __init__(self, message: str = "validation error") -> None:
        super().__init__(code="VALIDATION_ERROR", message=message, status_code=400)
