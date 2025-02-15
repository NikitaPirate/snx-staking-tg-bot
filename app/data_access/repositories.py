import uuid
from collections.abc import Iterable, Sequence
from typing import TypeVar

from eth_typing import Address
from sqlalchemy import BinaryExpression, Select, and_, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import SQLModel

from app.common import Chain
from app.models import Account, Chat, ChatAccount, Notif

M = TypeVar("M", bound=SQLModel)
# For PyCharm doesn't complain about type mismatches
BinaryCriteriaType = BinaryExpression | bool


class GenericSqlRepository[M]:
    _model: M

    def __init__(self, session: AsyncSession) -> None:
        self._session: AsyncSession = session

    async def is_exist(self, *criteria: BinaryCriteriaType) -> bool:
        query = select(self._assemble_query(*criteria).exists())
        res = await self._session.execute(query)
        return res.scalar()

    async def get_one_or_none(self, *criteria: BinaryCriteriaType) -> M | None:
        query = self._assemble_query(*criteria)
        res = await self._session.execute(query)
        return res.scalar_one_or_none()

    async def get_all(self, *criteria: BinaryCriteriaType) -> Sequence[M]:
        query = self._assemble_query(*criteria)
        res = await self._session.execute(query)
        return res.scalars().all()

    async def add(self, record: M) -> M:
        self._session.add(record)
        await self._session.flush()
        return record

    async def _insert_all(
        self,
        records: Iterable[M],
        on_conflict: str | None = None,
        conflict_target: list[str] | None = None,  # Fields to declare conflict
        update_fields: list[str] | None = None,
        chunk_size: int = 1000,
    ) -> None:
        if not records:
            return

        records_list = list(records)
        values = [
            {
                column.key: getattr(record, column.key)
                for column in record.__table__.columns
                if hasattr(record, column.key)
            }
            for record in records_list
        ]

        for i in range(0, len(values), chunk_size):
            chunk = values[i : i + chunk_size]
            stmt = pg_insert(self._model.__table__).values(chunk)

            if on_conflict == "ignore":
                stmt = stmt.on_conflict_do_nothing()
            elif on_conflict == "update":
                if not conflict_target or not update_fields:
                    raise ValueError(
                        "Should declare conflict_target and update_fields for on_conflict='update'"
                    )
                stmt = stmt.on_conflict_do_update(
                    index_elements=conflict_target,
                    set_={field: getattr(stmt.excluded, field) for field in update_fields},
                )

            await self._session.execute(stmt)

        await self._session.flush()

    async def insert_all(self, records: Iterable[M]) -> None:
        await self._insert_all(records)

    async def insert_all_ignore(self, records: Iterable[M], chunk_size: int = 1000) -> None:
        await self._insert_all(records, on_conflict="ignore", chunk_size=chunk_size)

    async def insert_all_update(
        self,
        records: Iterable[M],
        conflict_target: list[str] | None,
        update_fields: list[str] | None,
        chunk_size: int = 1000,
    ) -> None:
        await self._insert_all(
            records,
            on_conflict="update",
            conflict_target=conflict_target,
            update_fields=update_fields,
            chunk_size=chunk_size,
        )

    async def merge(self, record: M) -> M:
        return await self._session.merge(record)

    async def delete(self, record: M) -> None:
        await self._session.delete(record)
        await self._session.flush()

    def _assemble_query(self, *criteria: BinaryCriteriaType) -> Select:
        stmt = select(self._model)
        if criteria:
            stmt = stmt.where(and_(*criteria))
        return stmt


class GenericSqlRepositoryWithUUID(GenericSqlRepository[M]):
    async def get_by_id_or_none(self, id_: uuid.UUID) -> M:
        return await self.get_one_or_none(self._model.id == id_)

    async def get_all_by_ids(self, ids: Sequence[uuid.UUID]) -> Sequence[M]:
        return await self.get_all(self._model.id.in_(ids))

    async def get_ids(self, *criteria: BinaryCriteriaType) -> Sequence[uuid.UUID]:
        query = self._assemble_query(*criteria).with_only_columns(self._model.id)
        res = await self._session.execute(query)
        return [row[0] for row in res.all()]

    async def delete_by_id(self, id_: uuid.UUID):
        record = await self.get_by_id_or_none(id_)
        if record:
            await self.delete(record)


class AccountRepository(GenericSqlRepositoryWithUUID[Account]):
    _model = Account

    async def get_by_address_chain_or_none(
        self, address: Address | str, chain: Chain
    ) -> Account | None:
        return await self.get_one_or_none(
            self._model.address == address, self._model.chain == chain
        )

    async def get_all_addresses_for_chain(self, chain: Chain) -> Sequence[Address]:
        # noinspection PyTypeChecker
        query = select(self._model.address).where(self._model.chain == chain).distinct()
        result = await self._session.execute(query)
        return [row[0] for row in result.all()]


class ChatRepository(GenericSqlRepository[Chat]):
    _model = Chat


class ChatAccountRepository(GenericSqlRepositoryWithUUID[ChatAccount]):
    _model = ChatAccount


class NotifRepository(GenericSqlRepositoryWithUUID[Notif]):
    _model = Notif
