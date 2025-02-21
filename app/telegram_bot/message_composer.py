from uuid import UUID

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from app.common import SNXMultiChainData
from app.models import ChatAccount, Notif, NotifType
from app.telegram_bot import texts, utils
from app.telegram_bot.constants import NOTIF_TYPE_NAMES, Callbacks
from app.telegram_bot.utils import remaining_time_until


def start() -> str:
    text = """
👋 Welcome! I'm your personal SNX staking monitoring assistant.
💼 /accounts
📈 /dashboard
💸/payday
ℹ️ /info

Tutorial: https://medium.com/@nikita-k/telegram-bot-update-fd56d2931574
    """
    return text


def user_not_exist(received_command: str) -> str:
    text = f"To use {received_command} please first send /start."
    return text


def accounts_menu(chat_accounts: list[ChatAccount]) -> tuple[str, InlineKeyboardMarkup]:
    text = "ACCOUNTS MENU"
    buttons = utils.render_accounts_buttons(chat_accounts)
    buttons.append([InlineKeyboardButton(text="add", callback_data=Callbacks.ADD_ACCOUNT)])
    keyboard = InlineKeyboardMarkup(buttons)
    return text, keyboard


def account_menu() -> tuple[str, InlineKeyboardMarkup]:
    text = "ACCOUNT MENU"
    keyboard = [
        [
            InlineKeyboardButton(
                text="customize display", callback_data=Callbacks.CUSTOMIZE_DISPLAY
            )
        ],
        [InlineKeyboardButton(text="notifs", callback_data=Callbacks.ACCOUNT_NOTIFS)],
        [InlineKeyboardButton(text="delete", callback_data=Callbacks.DELETE_ACCOUNT)],
        [InlineKeyboardButton(text="accounts", callback_data=Callbacks.ACCOUNTS_MENU)],
    ]

    keyboard = InlineKeyboardMarkup(keyboard)
    return text, keyboard


def delete_account() -> tuple[str, InlineKeyboardMarkup]:
    text = "ACCOUNT DELETED"
    buttons = [
        [
            InlineKeyboardButton(text="Accounts", callback_data=Callbacks.ACCOUNTS_MENU),
            InlineKeyboardButton(text="Dashboard", callback_data=Callbacks.DASHBOARD),
        ]
    ]
    keyboard = InlineKeyboardMarkup(buttons)
    return text, keyboard


def customize_account_display_menu(link: ChatAccount) -> tuple[str, InlineKeyboardMarkup]:
    text = "ACCOUNT DISPLAY SETTINGS"

    def render_button(_setting_name: str, _enabled: bool) -> InlineKeyboardButton:
        _text = "✅{name}: enabled" if _enabled else "❌{name}: disabled"
        _text = _text.format(name=_setting_name)
        return InlineKeyboardButton(text=_text, callback_data=_setting_name)

    buttons = []
    for setting_name, enabled in link.account_settings.items():
        buttons.append([render_button(setting_name, enabled)])
    buttons.append(
        [
            InlineKeyboardButton(text="back", callback_data=Callbacks.ACCOUNT_MENU),
            InlineKeyboardButton(text="accounts", callback_data=Callbacks.ACCOUNTS_MENU),
        ],
    )
    keyboard = InlineKeyboardMarkup(buttons)
    return text, keyboard


def request_account_info() -> tuple[str, InlineKeyboardMarkup]:
    text = (
        "Send address and chain separated by space to start tracking account. Available chains: \n"
        "E, ETH, ethereum\n"
        "O, OP, optimism\n"
    )
    buttons = [
        [
            InlineKeyboardButton(text="accounts", callback_data=Callbacks.ACCOUNTS_MENU),
        ]
    ]
    keyboard = InlineKeyboardMarkup(buttons)
    return text, keyboard


def handle_account_info_incorrect() -> str:
    text = "incorrect data"
    return text


def handle_account_info_success(chat_account_id: UUID) -> tuple[str, InlineKeyboardMarkup]:
    text = "Account successfully added."
    keyboard = [
        [
            InlineKeyboardButton(text="dashboard", callback_data=Callbacks.DASHBOARD),
            InlineKeyboardButton(text="manage account", callback_data=str(chat_account_id)),
        ],
        [
            InlineKeyboardButton(text="accounts", callback_data=Callbacks.ACCOUNTS_MENU),
        ],
    ]
    keyboard = InlineKeyboardMarkup(keyboard)
    return text, keyboard


def account_notifs_menu(notifs: list[Notif]) -> tuple[str, InlineKeyboardMarkup]:
    text = "ACCOUNT NOTIFS MENU"
    buttons = []

    for notif in notifs:
        button_text = NOTIF_TYPE_NAMES[notif.type]
        if notif.type is NotifType.ratio:
            button_text += " above" if notif.params["above"] else " below"
            button_text += f" {round(notif.params['target'] * 100, 2)}%"
        button_text += " — delete"
        notif_button = [
            InlineKeyboardButton(
                text=f"{button_text}",
                callback_data=str(notif.id),
            )
        ]
        buttons.append(notif_button)
    buttons.append(
        [
            InlineKeyboardButton(text="create notif", callback_data=Callbacks.CREATE_NOTIF),
        ]
    )
    buttons.append(
        [
            InlineKeyboardButton(text="back", callback_data=Callbacks.ACCOUNT_MENU),
            InlineKeyboardButton(text="accounts", callback_data=Callbacks.ACCOUNTS_MENU),
        ]
    )
    keyboard = InlineKeyboardMarkup(buttons)
    return text, keyboard


def start_creating_notif() -> tuple[str, InlineKeyboardMarkup]:
    text = "SELECT NOTIF TYPE"
    buttons = []
    for notif_type in NotifType:
        buttons.append(
            [InlineKeyboardButton(text=NOTIF_TYPE_NAMES[notif_type], callback_data=notif_type)]
        )
    buttons.append(
        [
            InlineKeyboardButton(text="back", callback_data=Callbacks.ACCOUNT_NOTIFS),
            InlineKeyboardButton(text="accounts", callback_data=Callbacks.ACCOUNTS_MENU),
        ]
    )
    keyboard = InlineKeyboardMarkup(buttons)
    return text, keyboard


def request_notif_data_with_additional_data(selected_notif_type: NotifType) -> str:
    notif_data_request_ratio = """
    Send direction and target using keywords a(above) or b(below) and target.
    Example: a 499
    """
    notif_type_to_notif_data_request = {NotifType.ratio: notif_data_request_ratio}
    return notif_type_to_notif_data_request[selected_notif_type]


def create_notif(selected_account_address: str) -> tuple[str, InlineKeyboardMarkup]:
    text = "NOTIF CREATED"
    buttons = [
        [
            InlineKeyboardButton(
                text=f"{selected_account_address[:6]} notifs",
                callback_data=Callbacks.ACCOUNT_NOTIFS,
            ),
            InlineKeyboardButton(text="accounts", callback_data=Callbacks.ACCOUNTS_MENU),
        ],
    ]
    keyboard = InlineKeyboardMarkup(buttons)
    return text, keyboard


def create_notif_already_exists(selected_account_address: str) -> tuple[str, InlineKeyboardMarkup]:
    text = "NOTIF ALREADY EXISTS"
    buttons = [
        [
            InlineKeyboardButton(
                text=f"{selected_account_address[:6]} notifs",
                callback_data=Callbacks.ACCOUNT_NOTIFS,
            ),
            InlineKeyboardButton(text="accounts", callback_data=Callbacks.ACCOUNTS_MENU),
        ],
    ]
    keyboard = InlineKeyboardMarkup(buttons)
    return text, keyboard


def render_notif(notif: Notif) -> tuple[str, InlineKeyboardMarkup]:
    if notif.type == NotifType.ratio:
        direction = "above" if notif.params["above"] else "below"
        text = (
            f"{notif.account.address[:6]}... c-ratio {direction}"
            f" {round(notif.params['target'] * 100, 2)}%"
        )
    else:
        text = f"{notif.account.address[:6]}... {NOTIF_TYPE_NAMES[notif.type]}"
    buttons = [
        [
            InlineKeyboardButton(
                text="dashboard",
                callback_data=Callbacks.DASHBOARD,
            ),
        ]
    ]
    keyboard = InlineKeyboardMarkup(buttons)
    return text, keyboard


def info() -> str:
    text = texts.info_command
    return text.replace(".", "\\.").replace("-", "\\-").replace("(", "\\(").replace(")", "\\)")


def payday(snx_data: SNXMultiChainData) -> str:
    text = ""
    for chain, period_end in snx_data.period_end_times().items():
        remaining_time = remaining_time_until(period_end)
        text += f"{chain}: {remaining_time}\n"
    return text
