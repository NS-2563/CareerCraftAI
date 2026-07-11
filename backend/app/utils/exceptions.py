from fastapi import HTTPException, status


class AppException(HTTPException):
    """Base application exception."""

    def __init__(
        self,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        message: str = "An error occurred",
        errors: list = None,
    ):
        super().__init__(status_code=status_code, detail={"message": message, "errors": errors})


class NotFoundException(AppException):
    """Exception for resource not found."""

    def __init__(self, resource: str = "Resource", identifier: str = None):
        message = f"{resource} not found"
        if identifier:
            message += f" with id: {identifier}"
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            message=message,
        )


class UnauthorizedException(AppException):
    """Exception for unauthorized access."""

    def __init__(self, message: str = "Unauthorized access"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message=message,
        )


class ForbiddenException(AppException):
    """Exception for forbidden access."""

    def __init__(self, message: str = "Access forbidden"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            message=message,
        )


class ValidationException(AppException):
    """Exception for validation errors."""

    def __init__(self, message: str = "Validation error", errors: list = None):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            message=message,
            errors=errors,
        )


class ConflictException(AppException):
    """Exception for resource conflict."""

    def __init__(self, message: str = "Resource already exists"):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            message=message,
        )


class InternalServerException(AppException):
    """Exception for internal server errors."""

    def __init__(self, message: str = "Internal server error"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=message,
        )


# Exception handlers
def register_exception_handlers(app):
    """Register global exception handlers."""
    from fastapi import Request
    from fastapi.responses import JSONResponse

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "message": exc.detail.get("message") if isinstance(exc.detail, dict) else str(exc.detail),
                "errors": exc.detail.get("errors") if isinstance(exc.detail, dict) else None,
            },
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": "Internal server error",
            },
        )