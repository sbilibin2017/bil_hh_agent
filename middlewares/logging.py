import logging
import time
from typing import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        method = request.method
        url = str(request.url)
        logger.info(f"Request:\n  Method: {method}\n  URL: {url}")

        start_time = time.time()
        response: Response = await call_next(request)
        process_time = time.time() - start_time

        # Получаем размер ответа
        content_length: int
        if response.headers.get("content-length") is not None:
            try:
                content_length = int(response.headers.get("content-length", "0"))
            except ValueError:
                content_length = 0
        else:
            # Если длина не указана, читаем тело
            body_bytes = b""
            async for chunk in response.body_iterator:  # type: ignore
                body_bytes += chunk
            content_length = len(body_bytes)

            # Воссоздаем response, чтобы клиент получил тело
            response = Response(
                content=body_bytes,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type,
            )

        logger.info(
            f"Response:\n"
            f"  Method: {method}\n"
            f"  URL: {url}\n"
            f"  Status: {response.status_code}\n"
            f"  Size: {content_length} bytes\n"
            f"  Time: {process_time:.3f}s"
        )

        return response
