from time import perf_counter
from uuid import uuid4

from fastapi import Request, Response

from app.utils.logger import get_logger, reset_request_id, set_request_id

logger = get_logger(__name__)


async def request_context_middleware(request: Request, call_next) -> Response:
    request_id = str(uuid4())
    request_token = set_request_id(request_id)
    start_time = perf_counter()
    response: Response | None = None

    try:
        response = await call_next(request)
        return response
    except Exception:
        duration_ms = round((perf_counter() - start_time) * 1000, 2)
        logger.exception(
            "http_request",
            status=500,
            duration_ms=duration_ms,
            method=request.method,
            path=request.url.path,
            query=str(request.url.query),
        )
        raise
    finally:
        if response is not None:
            response.headers["X-Request-ID"] = request_id
            duration_ms = round((perf_counter() - start_time) * 1000, 2)
            logger.info(
                "http_request",
                status=response.status_code,
                duration_ms=duration_ms,
                method=request.method,
                path=request.url.path,
                query=str(request.url.query),
            )

        reset_request_id(request_token)
