from fastapi import Request
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from backend.db.db import DBContext


class TxMiddleware(BaseHTTPMiddleware):
    """
    Middleware для управления транзакциями с использованием DBContext.
    Для каждого запроса создается сессия, которая коммитится при успешном
    выполнении запроса и откатывается в случае ошибки.
    """

    def __init__(self, db_context: DBContext):
        """
        Инициализация middleware с DBContext.

        :param db_context: Контекст базы данных с фабрикой AsyncSession
        """
        super().__init__()
        self.db_context = db_context

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        session: AsyncSession = await self.db_context.get_session()
        try:
            response = await call_next(request)
            await session.commit()
            return response
        except SQLAlchemyError:
            await session.rollback()
            raise
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
            self.db_context.reset()
