import re
from warnings import filterwarnings

from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)
from telegram.warnings import PTBUserWarning

from app.models import ChatAccountSettings, NotifType
from app.telegram_bot import commands
from app.telegram_bot.constants import Callbacks, States

filterwarnings(action="ignore", message=r".*CallbackQueryHandler", category=PTBUserWarning)


def callback(_callback: str) -> str:
    return "^" + _callback + "$"


uuid_pattern = "^[0-9a-f]{8}-[0-9a-f]{4}-[0-5][0-9a-f]{3}-[089ab][0-9a-f]{3}-[0-9a-f]{12}$"
account_settings_fields_pattern = "|".join(
    re.escape(key) for key in ChatAccountSettings.__annotations__
)
notif_type_pattern = "|".join(re.escape(_type) for _type in NotifType)


notifs_conv = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(
            commands.account_notifs_menu, pattern=callback(Callbacks.ACCOUNT_NOTIFS)
        ),
    ],
    states={
        States.ACCOUNT_NOTIFS_MENU: [
            CallbackQueryHandler(commands.delete_notif, pattern=uuid_pattern),
            CallbackQueryHandler(
                commands.start_creating_notif, pattern=callback(Callbacks.CREATE_NOTIF)
            ),
            CallbackQueryHandler(commands.account_menu, pattern=callback(Callbacks.ACCOUNT_MENU)),
        ],
        States.SELECT_NOTIF_TYPE_TO_CREATE: [
            CallbackQueryHandler(commands.request_notif_data, pattern=notif_type_pattern)
        ],
        States.HANDLE_NOTIF_INFO: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, commands.create_notif),
        ],
        States.NOTIF_CREATED: [
            CallbackQueryHandler(
                commands.account_notifs_menu, pattern=callback(Callbacks.ACCOUNT_NOTIFS)
            ),
        ],
    },
    fallbacks=[CommandHandler("stop", commands.stop)],
    map_to_parent={States.ACCOUNT_MENU: States.ACCOUNT_MENU},
    allow_reentry=True,
    # persistent=True,
    name="notifs_conv",
)

accounts_conv = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(commands.accounts_menu, pattern=Callbacks.ACCOUNTS_MENU),
        CommandHandler("accounts", commands.accounts_menu),
    ],
    states={
        States.ACCOUNTS_MENU: [
            CallbackQueryHandler(commands.request_account_info, pattern=Callbacks.ADD_ACCOUNT),
            CallbackQueryHandler(commands.account_menu, pattern=uuid_pattern),
        ],
        States.ACCOUNT_MENU: [
            CallbackQueryHandler(
                commands.customize_account_display_menu,
                pattern=Callbacks.CUSTOMIZE_DISPLAY,
            ),
            notifs_conv,
            CallbackQueryHandler(commands.accounts_menu, pattern=Callbacks.ACCOUNTS_MENU),
            CallbackQueryHandler(commands.delete_account, pattern=Callbacks.DELETE_ACCOUNT),
        ],
        States.CUSTOMIZE_ACCOUNT_DISPLAY: [
            CallbackQueryHandler(
                commands.handle_account_setting_change,
                pattern=account_settings_fields_pattern,
            ),
            CallbackQueryHandler(commands.account_menu, pattern=Callbacks.ACCOUNT_MENU),
            CallbackQueryHandler(commands.accounts_menu, pattern=Callbacks.ACCOUNTS_MENU),
        ],
        States.HANDLE_ACCOUNT_INFO: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, commands.process_account_creating),
            CallbackQueryHandler(commands.accounts_menu, pattern=Callbacks.ACCOUNTS_MENU),
            CallbackQueryHandler(commands.account_menu, pattern=Callbacks.ACCOUNT_MENU),
        ],
        States.ACCOUNT_ADDED: [
            CallbackQueryHandler(commands.account_menu, pattern=uuid_pattern),
            CallbackQueryHandler(commands.dashboard, pattern=callback(Callbacks.DASHBOARD)),
            CallbackQueryHandler(
                commands.accounts_menu, pattern=callback(Callbacks.ACCOUNTS_MENU)
            ),
        ],
    },
    fallbacks=[CommandHandler("stop", commands.stop)],
    allow_reentry=True,
    # persistent=True,
    name="accounts_conv",
)

start_handler = CommandHandler("start", commands.start)
dash_command_handler = CommandHandler("dashboard", commands.dashboard)
dash_callback_handler = CallbackQueryHandler(commands.dashboard, pattern=Callbacks.DASHBOARD)
info_handler = CommandHandler("info", commands.info)
payday_handler = CommandHandler("payday", commands.payday)

handlers = [
    start_handler,
    info_handler,
    accounts_conv,
    notifs_conv,
    dash_command_handler,
    dash_callback_handler,
    payday_handler,
]
