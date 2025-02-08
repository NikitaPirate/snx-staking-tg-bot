import datetime
import uuid

from pydantic import condecimal
from sqlalchemy import text
from sqlmodel import Field, SQLModel

from app.common import Chain


class UUIDModel(SQLModel, table=False):
    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
        nullable=False,
        sa_column_kwargs={"server_default": text("gen_random_uuid()"), "unique": True},
    )

    def __hash__(self) -> int:
        return hash(self.id)


class Account(UUIDModel, table=True):
    address: str = Field(index=True)
    chain: Chain = Field()
    c_ratio: float = Field(default=0)
    snx_count: condecimal(max_digits=50, decimal_places=0) = Field(default=0)
    collateral: condecimal(max_digits=50, decimal_places=0) = Field(default=0)
    sds_count: condecimal(max_digits=50, decimal_places=0) = Field(default=0)
    debt: condecimal(max_digits=50, decimal_places=0) = Field(default=0)
    claimable_snx: condecimal(max_digits=50, decimal_places=0) = Field(default=0)
    liquidation_deadline: datetime.datetime | None = Field(default=None)
