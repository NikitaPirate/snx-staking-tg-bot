import logging

from telegram import Bot
from telegram.error import BadRequest

from app.common import SNXMultiChainData
from app.data_access import UOWFactoryType
from app.models import Chat

logger = logging.getLogger(__name__)


def compose_dashboard_message(chat: Chat, snx_data: SNXMultiChainData) -> str:
    text = f"SNX Price: ${snx_data.format_snx_price()} \n\n"
    for link in chat.chat_accounts:
        account = link.account
        settings = link.account_settings
        if not account.inited:
            text += "Not initialized yet. This may take up to 10 minutes.\n\n"
            continue
        if settings["address"]:
            text += f"{account.address[:6]}... {account.chain}\n"
        if settings["c_ratio"]:
            text += f"C-ratio: {round(account.c_ratio * 100, 1)}%\n"
        if settings["collateral"]:
            snx_count = round(account.snx_count / 10**18, 2)
            collateral = round(account.collateral / 10**36, 2)
            text += f"Collateral: {snx_count} SNX = ${collateral}\n"
        if settings["debt"]:
            text += f"Debt: {round(account.debt / 10**18, 2)} sUSD\n"
        if settings["claimable_snx"]:
            text += f"Claimable SNX: {round(account.claimable_snx / 10**18, 2)}\n"
        if settings["liquidation_deadline"]:
            if not account.liquidation_deadline:
                liquidation_text = "Not flagged for liquidation"
            else:
                liquidation_text = f"Liquidation deadline: {
                    account.liquidation_deadline.strftime('%Y-%m-%d %H:%M:%S')
                }"
            text += liquidation_text + "\n"
        text += "\n"
    return text


async def update_dashboard_message(
    bot: Bot,
    chat_id: int,
    uow_factory: UOWFactoryType,
    snx_data: SNXMultiChainData,
) -> None:
    async with uow_factory() as uow:
        chat = await uow.chats.get_one_or_none(Chat.id == chat_id)
        if not chat.dashboard_message_id:
            return
    text = compose_dashboard_message(chat, snx_data)
    try:
        await bot.edit_message_text(text, chat.id, chat.dashboard_message_id)
    except BadRequest as e:
        if "Message to edit not found" in e.message:
            async with uow_factory() as uow:
                chat = await uow.chats.get_one_or_none(Chat.id == chat_id)
                chat.dashboard_message_id = None
        elif "Message is not modified:" in e.message:
            pass
        else:
            logger.exception("Unexpected error while dashboard update:", exc_info=e)
    except Exception as e:
        logger.exception("Unexpected error while dashboard update:", exc_info=e)
