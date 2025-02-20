import asyncio
import logging
from uuid import UUID

from telegram import Bot, InlineKeyboardMarkup
from telegram.error import Forbidden

from app.common import SNXMultiChainData
from app.data_access import UOWFactoryType
from app.models import Account, Notif, NotifType
from app.telegram_bot import message_composer
from app.telegram_bot.dashboard import update_dashboard_message

logger = logging.getLogger(__name__)


class AccountUpdateProcessor:
    def __init__(
        self,
        bot: Bot,
        uow_factory: UOWFactoryType,
        snx_data: SNXMultiChainData,
        updated_account_queue: asyncio.Queue,
    ):
        self._uow_factory: UOWFactoryType = uow_factory
        self._bot: Bot = bot
        self._snx_data: SNXMultiChainData = snx_data
        self._updated_account_queue: asyncio.Queue = updated_account_queue
        self._satisfied = {
            NotifType.ratio: self._ratio_satisfied,
            NotifType.rewards_claimable: self._rewards_claimable_satisfied,
            NotifType.rewards_claimed: self._rewards_claimed_satisfied,
            NotifType.flagged_for_liquidation: self._flagged_for_liquidation_satisfied,
        }

    # NOTIFS
    @staticmethod
    def _ratio_satisfied(notif: Notif) -> bool:
        above, target, current = (
            notif.params["above"],
            notif.params["target"],
            notif.account.c_ratio,
        )
        return (above and current > target) or (not above and current < target)

    def _rewards_claimable_satisfied(self, notif: Notif) -> bool:
        account = notif.account
        if not account.claimable_snx:
            return False

        issuance_ratio = self._snx_data[account.chain].issuance_ratio
        ratio_threshold = issuance_ratio * 0.9902  # found experimentally
        return account.c_ratio > ratio_threshold

    @staticmethod
    def _rewards_claimed_satisfied(notif: Notif) -> bool:
        return notif.account.claimable_snx == 0

    @staticmethod
    def _flagged_for_liquidation_satisfied(notif: Notif) -> bool:
        return notif.account.liquidation_deadline is not None

    async def _send_notif(self, notif: Notif) -> tuple[int, str] | None:
        """:returns: int sent_message_id"""
        text, keyboard = message_composer.render_notif(notif)
        chat = notif.chat

        try:
            sent_message = await self._bot.send_message(
                chat_id=chat.id, text=text, reply_markup=keyboard
            )
            if chat.sent_notif_message_id:
                await self._bot.edit_message_text(
                    chat.sent_notif_message_text,
                    chat.id,
                    chat.sent_notif_message_id,
                    reply_markup=InlineKeyboardMarkup([]),
                )
            return sent_message.id, text
        except Forbidden:
            return

    async def _process_notif(self, notif_id: UUID):
        async with self._uow_factory() as uow:
            if not (notif := await uow.notifs.get_by_id_or_none(notif_id)):
                return
            if notif.enabled and self._satisfied[notif.type](notif):
                message_details = await self._send_notif(notif)
                if not message_details:
                    await uow.chats.delete(notif.chat)
                    return
                sent_message_id, text = message_details
                notif.chat.sent_notif_message_id = sent_message_id
                notif.chat.sent_notif_message_text = text
                notif.enabled = False
            if not notif.enabled and not self._satisfied[notif.type](notif):
                notif.enabled = True

    async def _process_account_notifs(self, account: Account):
        for chat_account in account.chat_accounts:
            for notif in chat_account.notifs:
                await self._process_notif(notif.id)

    # DASHBOARD
    async def _update_dashboard(self, account: Account):
        for chat_account in account.chat_accounts:
            await update_dashboard_message(
                self._bot, chat_account.chat_id, self._uow_factory, self._snx_data
            )

    # WORKER
    async def worker(self):
        while True:
            # noinspection PyBroadException
            try:
                account_id = await self._updated_account_queue.get()
                async with self._uow_factory() as uow:
                    if not (account := await uow.accounts.get_by_id_or_none(account_id)):
                        continue
                await asyncio.gather(
                    self._update_dashboard(account),
                    self._process_account_notifs(account),
                    return_exceptions=True,
                )
            except asyncio.CancelledError:
                pass
            except Exception as e:
                logger.error("Unexpected exception in worker", exc_info=e)
