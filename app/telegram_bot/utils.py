import datetime

from eth_typing import AnyAddress
from eth_utils import is_address, to_checksum_address
from telegram import InlineKeyboardButton

from app.common import Chain
from app.models import ChatAccount, NotifParams, NotifType


def parse_account_info_message(message: str) -> tuple[AnyAddress, Chain]:
    address, chain = None, None
    for word in message.split():
        if word.startswith("0x"):
            if is_address(word):
                address = to_checksum_address(word)
        else:
            chain = Chain.from_string(word)

    return address, chain


def parse_notif_info_message(notif_type: NotifType, message: str) -> NotifParams:
    args = message.split()
    if notif_type is NotifType.ratio:
        above = {"a": True, "above": True, "b": False, "below": False}[args[0].lower()]
        target = float(args[1]) / 100
        return NotifParams(above=above, target=target)


def render_accounts_buttons(chat_accounts: list[ChatAccount]) -> list[list[InlineKeyboardButton]]:
    buttons = []
    for chat_account in chat_accounts:
        account = chat_account.account
        account_button = [
            InlineKeyboardButton(
                text=f"{account.address[:6]}... {account.chain}",
                callback_data=str(account.id),
            )
        ]
        buttons.append(account_button)
    return buttons


def remaining_time_until(timestamp: float) -> str:
    text = ""
    remaining_seconds = timestamp - datetime.datetime.now().timestamp()

    if remaining_seconds < 0:
        text += "–"
        remaining_seconds = abs(remaining_seconds)

    days, seconds = divmod(remaining_seconds, 86400)
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    parts = [(days, "D"), (hours, "H"), (minutes, "M"), (seconds, "S")]
    non_zero_parts = []

    for part in parts:
        if part[0] != 0 or non_zero_parts:
            non_zero_parts.append(part)

    return text + ":".join(f"{int(value)}{label}" for value, label in non_zero_parts)
