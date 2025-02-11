import datetime
import uuid
from enum import StrEnum
from typing import TypedDict

from pydantic import condecimal
from sqlalchemy import BigInteger, PrimaryKeyConstraint, text
from sqlmodel import Field, Relationship, SQLModel

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
    c_ratio: float = Field(default=0, sa_column_kwargs={"server_default": "0"})
    snx_count: condecimal(max_digits=50, decimal_places=0) = Field(
        default=0, sa_column_kwargs={"server_default": "0"}
    )
    collateral: condecimal(max_digits=50, decimal_places=0) = Field(
        default=0, sa_column_kwargs={"server_default": "0"}
    )
    sds_count: condecimal(max_digits=50, decimal_places=0) = Field(
        default=0, sa_column_kwargs={"server_default": "0"}
    )
    debt: condecimal(max_digits=50, decimal_places=0) = Field(
        default=0, sa_column_kwargs={"server_default": "0"}
    )
    claimable_snx: condecimal(max_digits=50, decimal_places=0) = Field(
        default=0, sa_column_kwargs={"server_default": "0"}
    )
    liquidation_deadline: datetime.datetime | None = Field(default=None)

    chat_links: list["ChatAccountLink"] = Relationship(
        back_populates="account",
        sa_relationship_kwargs={"lazy": "selectin", "cascade": "all, delete-orphan"},
    )

    notifs: list["Notif"] = Relationship(
        back_populates="account",
        sa_relationship_kwargs={
            "lazy": "selectin",
            "cascade": "all, delete-orphan",
            "passive_deletes": True,
        },
    )


class ChatAccountSettings(TypedDict):
    address: bool
    c_ratio: bool
    collateral: bool
    debt: bool
    claimable_snx: bool
    liquidation_deadline: bool


DEFAULT_CHAT_ACCOUNT_SETTINGS: ChatAccountSettings = {
    "address": False,
    "c_ratio": True,
    "collateral": False,
    "debt": False,
    "claimable_snx": False,
    "liquidation_deadline": False,
}


class ChatAccountLink(SQLModel, table=True):
    __table_args__ = (
        PrimaryKeyConstraint(
            "chat_id",
            "account_id",
            name="pk_chat_account_link",  # явное имя PK
        ),
    )

    chat_id: int | None = Field(default=None, foreign_key="chat.id")
    account_id: uuid.UUID | None = Field(default=None, foreign_key="account.id")
    account_settings: ChatAccountSettings = Field(
        default_factory=lambda: DEFAULT_CHAT_ACCOUNT_SETTINGS.copy()
    )

    chat: "Chat" = Relationship(back_populates="account_links")
    account: "Account" = Relationship(back_populates="chat_links")

    def update_settings(self, **kwargs: bool) -> None:
        # noinspection PyTypeChecker
        self.account_settings = {**self.account_settings, **kwargs}

    def __hash__(self) -> int:
        return hash(f"{self.chat_id}-{self.account_id}")


class Chat(SQLModel, table=True):
    id: int = Field(primary_key=True, index=True, nullable=False, sa_type=BigInteger)
    dashboard_message_id: int = Field()
    sent_notif_message_id: int = Field()
    sent_notif_message_text: str = Field()

    account_links: list["ChatAccountLink"] = Relationship(
        back_populates="chat",
        sa_relationship_kwargs={
            "lazy": "selectin",
            "cascade": "all, delete-orphan",
        },
    )

    notifs: list["Notif"] = Relationship(
        back_populates="chat",
        sa_relationship_kwargs={
            "lazy": "selectin",
            "cascade": "all, delete-orphan",
        },
    )


# NOTIF


class NotifType(StrEnum):
    ratio = "ratio"
    rewards_claimable = "rewards_claimable"
    rewards_claimed = "rewards_claimed"
    flagged_for_liquidation = "flagged_for_liquidation"


class NotifParams(TypedDict):
    above: bool | None
    target: float | None


class Notif(UUIDModel, table=True):
    type: NotifType = Field()
    params: NotifParams = Field(default={})
    enabled: bool = Field(default=True)
    onetime: bool = Field(default=False)
    account_id: uuid.UUID = Field(
        foreign_key="account.id", sa_column_kwargs={"ondelete": "CASCADE"}
    )
    chat_id: int | None = Field(foreign_key="chat.id", sa_column_kwargs={"ondelete": "CASCADE"})

    account: Account = Relationship(back_populates="notifs")
    chat: Chat = Relationship(back_populates="notifs")

    def update_params(self, **kwargs: bool) -> None:
        # noinspection PyTypeChecker
        self.params = {**self.params, **kwargs}
