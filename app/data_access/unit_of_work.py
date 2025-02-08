import asyncio
from collections.abc import Callable
from typing import Self

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.data_access.repositories import AccountRepository


class UnitOfWork:
    def __init__(self, session_factory: async_sessionmaker) -> None:
        self._session_factory: async_sessionmaker = session_factory

    async def __aenter__(self) -> Self:
        self._session: AsyncSession = self._session_factory()
        self.accounts: AccountRepository = AccountRepository(self._session)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:  # noqa: ANN001
        await asyncio.sleep(0)
        try:
            if exc_val:
                await self.rollback()
            else:
                await self.commit()
        finally:
            await self._close()

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()

    async def _close(self) -> None:
        await asyncio.shield(self._session.close())


UOWFactoryType = Callable[[], UnitOfWork]


def uow_factory_maker(session_factory: async_sessionmaker) -> UOWFactoryType:
    def _create_uow() -> UnitOfWork:
        return UnitOfWork(session_factory)

    return _create_uow
