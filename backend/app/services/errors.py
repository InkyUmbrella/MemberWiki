class ServiceError(Exception):
    code = "SERVICE_ERROR"
    status_code = 400


class UnauthorizedError(ServiceError):
    code = "UNAUTHORIZED"
    status_code = 401


class ConflictError(ServiceError):
    code = "CONFLICT"
    status_code = 409


class NotFoundError(ServiceError):
    code = "NOT_FOUND"
    status_code = 404


class ForbiddenError(ServiceError):
    code = "FORBIDDEN"
    status_code = 403


class ValidationError(ServiceError):
    code = "VALIDATION_ERROR"
    status_code = 400
