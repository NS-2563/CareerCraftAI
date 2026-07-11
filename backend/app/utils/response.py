from typing import Any, Optional
from fastapi.responses import JSONResponse
from fastapi import status


def success_response(
    data: Any = None,
    message: str = "Success",
    status_code: int = status.HTTP_200_OK,
    **kwargs
) -> JSONResponse:
    """Create a standardized success response."""
    content = {
        "success": True,
        "message": message,
    }
    if data is not None:
        content["data"] = data
    content.update(kwargs)
    return JSONResponse(content=content, status_code=status_code)


def error_response(
    message: str = "An error occurred",
    status_code: int = status.HTTP_400_BAD_REQUEST,
    errors: Optional[list] = None,
    **kwargs
) -> JSONResponse:
    """Create a standardized error response."""
    content = {
        "success": False,
        "message": message,
    }
    if errors:
        content["errors"] = errors
    content.update(kwargs)
    return JSONResponse(content=content, status_code=status_code)


def created_response(
    data: Any = None,
    message: str = "Created successfully",
    **kwargs
) -> JSONResponse:
    """Create a 201 Created response."""
    return success_response(data=data, message=message, status_code=status.HTTP_201_CREATED, **kwargs)


def deleted_response(message: str = "Deleted successfully") -> JSONResponse:
    """Create a 204 No Content response (as 200 with message)."""
    return success_response(message=message, status_code=status.HTTP_200_OK)


def paginated_response(
    items: list,
    total: int,
    page: int,
    page_size: int,
    message: str = "Success"
) -> JSONResponse:
    """Create a paginated response."""
    total_pages = (total + page_size - 1) // page_size
    return success_response(
        data={
            "items": items,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1,
            }
        },
        message=message
    )