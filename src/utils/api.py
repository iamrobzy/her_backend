from fastapi.responses import JSONResponse


def format_error_response(error_message: str, status_code: int = 500):
    return JSONResponse(
        status_code=status_code,
        content={"status": "error", "data": None, "message": error_message},
    )
