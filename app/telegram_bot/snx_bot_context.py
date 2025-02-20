import asyncio
from collections.abc import Callable
from functools import wraps
from typing import NotRequired, TypedDict, TypeVar
from uuid import UUID

from eth_typing import AnyAddress
from telegram.ext import Application, CallbackContext, ExtBot

from app.common import Chain, SNXMultiChainData
from app.data_access import UnitOfWork, UOWFactoryType
from app.models import Account, Chat, ChatAccount, Notif, NotifType

T = TypeVar("T")


class NotFoundError(Exception):
    def __init__(self, entity: str):
        super().__init__(f"{entity} not found")


def with_uow(func: Callable[..., T]) -> Callable[..., T]:
    @wraps(func)
    async def wrapper(self, *args, **kwargs) -> T:  # noqa
        async with self.uow_factory() as uow:
            return await func(self, *args, uow=uow, **kwargs)

    return wrapper


class ChatData(TypedDict):
    selected_chat_account: NotRequired[UUID]
    notif_type: NotRequired[NotifType]


class BotData(TypedDict):
    snx_data: SNXMultiChainData
    uow_factory: UOWFactoryType
    new_accounts_queues: dict[Chain, asyncio.Queue[AnyAddress]]


class SnxBotContext(CallbackContext[ExtBot, dict, ChatData, BotData]):
    chat_data: ChatData
    bot_data: BotData

    def __init__(
        self,
        application: Application,
        chat_id: int | None = None,
        user_id: int | None = None,
    ):
        super().__init__(application=application, chat_id=chat_id, user_id=user_id)

    @property
    def uow_factory(self) -> UOWFactoryType:
        return self.bot_data["uow_factory"]

    @property
    def snx_data(self) -> SNXMultiChainData:
        return self.bot_data["snx_data"]

    @with_uow
    async def get_chat(self, *, uow: UnitOfWork) -> Chat:
        """Gets current chat or raises ChatNotFoundError"""
        chat = await uow.chats.get_one_or_none(Chat.id == self._chat_id)
        if chat is None:
            raise NotFoundError("Chat")
        return chat

    @with_uow
    async def create_chat_if_not_exists(self, *, uow: UnitOfWork) -> Chat:
        """Creates chat if it doesn't exist, otherwise returns existing one"""
        if not await uow.chats.is_exist(Chat.id == self._chat_id):
            chat = Chat(id=self._chat_id)
            await uow.chats.add(chat)

    @with_uow
    async def get_current_chat_account(self, *, uow: UnitOfWork) -> ChatAccount:
        """Gets current chat or raises ChatNotFoundError"""
        chat_account = await uow.chat_accounts.get_by_id_or_none(
            self.chat_data["selected_chat_account"]
        )
        if chat_account is None:
            raise NotFoundError("ChatAccount")
        return chat_account

    @with_uow
    async def process_account_creating(
        self, address: AnyAddress, chain: Chain, *, uow: UnitOfWork
    ) -> ChatAccount:
        if not (account := await uow.accounts.get_by_address_chain_or_none(address, chain)):
            account = Account(address=address, chain=chain)
            account = await uow.accounts.add(account)
            await self.bot_data["new_accounts_queues"][chain].put(address)
        if not (
            chat_account := await uow.chat_accounts.is_exist(
                ChatAccount.chat_id == self._chat_id, ChatAccount.account_id == account.id
            )
        ):
            chat_account = ChatAccount(chat_id=self._chat_id, account_id=account.id)
            await uow.accounts.add(chat_account)
        return chat_account

    @with_uow
    async def delete_current_chat_account(self, uow: UnitOfWork):
        await uow.chat_accounts.delete_by_id(self.chat_data.pop("selected_chat_account"))

    @with_uow
    async def toggle_current_chat_account_setting(self, setting_name: str, *, uow: UnitOfWork):
        chat_account = await self.get_current_chat_account(uow)
        chat_account.update_settings(
            **{setting_name: not chat_account.account_settings[setting_name]}
        )

    @with_uow
    async def create_notif(
        self,
        notif_type: NotifType,
        notif_params: dict,
        chat_account: ChatAccount,
        *,
        uow: UnitOfWork,
    ) -> tuple[bool, Notif | None]:
        if await uow.notifs.is_exist(
            Notif.chat_account == chat_account,
            Notif.type == notif_type,
            Notif.params == notif_params,
        ):
            return True, None

        notif = Notif(type=notif_type, chat_account=chat_account, params=notif_params)
        notif = await uow.notifs.add(notif)
        return False, notif

    @with_uow
    async def delete_notif_by_id(self, notif_id: UUID, *, uow: UnitOfWork):
        await uow.notifs.delete_by_id(notif_id)
