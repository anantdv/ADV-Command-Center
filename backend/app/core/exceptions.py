class AppError(Exception):
    def __init__(self, message: str, status_code: int = 400, details: dict | None = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


class PermissionDenied(AppError):
    def __init__(self, message: str = "Permission denied", details: dict | None = None):
        super().__init__(message, 403, details)


class FrappeClientError(AppError):
    pass


class AuthenticationError(AppError):
    def __init__(self, message: str = "Authentication required", details: dict | None = None):
        super().__init__(message, 401, details)


class FrappeUnavailableError(AppError):
    def __init__(self, message: str = "Frappe server is unavailable", details: dict | None = None):
        super().__init__(message, 502, details)
