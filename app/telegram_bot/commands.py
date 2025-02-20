from collections.abc import Callable
from uuid import UUID

from telegram import Message, Update
from telegram.ext import ConversationHandler

from app.models import NotifType
from app.telegram_bot import message_composer, utils
from app.telegram_bot.constants import States
from app.telegram_bot.dashboard import compose_dashboard_message, update_dashboard_message
from app.telegram_bot.snx_bot_context import SnxBotContext


def _get_message_delivery(update: Update) -> Callable:
    message_delivery: Callable = (
        update.callback_query.edit_message_text
        if update.callback_query
        else update.effective_chat.send_message
    )
    return message_delivery


async def start(update: Update, context: SnxBotContext):
    await context.create_chat_if_not_exists()
    text = message_composer.start()
    await context.bot.send_message(chat_id=update.effective_chat.id, text=text)


# STOP
async def stop(update: Update, _: SnxBotContext) -> int:
    """Need for conversation handler"""
    await update.effective_chat.send_message("Okay, bye.")
    return ConversationHandler.END


async def dashboard(update: Update, context: SnxBotContext) -> int:
    message_delivery: Callable = _get_message_delivery(update)
    chat = await context.get_chat()
    text = compose_dashboard_message(chat, context.snx_data)
    res: Message = await message_delivery(text=text)

    async with context.uow_factory() as uow:
        chat = await uow.merge(chat)
        chat.dashboard_message_id = res.message_id
    return ConversationHandler.END


# ACCOUNT CONVERSATION COMMANDS
async def accounts_menu(update: Update, context: SnxBotContext) -> str:
    message_delivery: Callable = _get_message_delivery(update)
    chat = await context.get_chat()
    text, keyboard = message_composer.accounts_menu(chat.chat_accounts)
    await message_delivery(text=text, reply_markup=keyboard)
    return States.ACCOUNTS_MENU


async def account_menu(update: Update, context: SnxBotContext) -> str:
    if update.callback_query and update.callback_query.data:
        context.chat_data["selected_chat_account"] = UUID(update.callback_query.data)
    text, keyboard = message_composer.account_menu()
    await update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
    return States.ACCOUNT_MENU


async def delete_account(update: Update, context: SnxBotContext) -> int:
    await context.delete_current_chat_account()
    text, keyboard = message_composer.delete_account()
    await update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
    return ConversationHandler.END


async def customize_account_display_menu(update: Update, context: SnxBotContext) -> str:
    """Loads account settings from db and render buttons"""

    chat_account = await context.get_current_chat_account()
    text, keyboard = message_composer.customize_account_display_menu(chat_account)
    await update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
    if chat_account.chat.dashboard_message_id:
        await update_dashboard_message(
            context.bot, chat_account.chat_id, context.uow_factory, context.snx_data
        )
    return States.CUSTOMIZE_ACCOUNT_DISPLAY


async def handle_account_setting_change(update: Update, context: SnxBotContext) -> str:
    setting = update.callback_query.data
    await context.toggle_current_chat_account_setting(setting)
    return await customize_account_display_menu(update, context)


async def request_account_info(update: Update, _: SnxBotContext) -> str:
    text, keyboard = message_composer.request_account_info()
    await update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
    return States.HANDLE_ACCOUNT_INFO


async def process_account_creating(update: Update, context: SnxBotContext) -> str:
    # 1. parse message. return what is incorrect and retry
    address, chain = utils.parse_account_info_message(update.message.text)
    if not all((address, chain)):
        text = message_composer.handle_account_info_incorrect()
        await update.effective_chat.send_message(text=text)
        return States.HANDLE_ACCOUNT_INFO
    # 2. process
    chat_account = await context.process_account_creating(address, chain)
    # 5. send message
    text, keyboard = message_composer.handle_account_info_success(chat_account.id)
    await update.effective_chat.send_message(text=text, reply_markup=keyboard)
    return States.ACCOUNT_ADDED


# NOTIFS CONVERSATION COMMANDS
async def account_notifs_menu(update: Update, context: SnxBotContext) -> str:
    chat_account = await context.get_current_chat_account()
    text, keyboard = message_composer.account_notifs_menu(chat_account.notifs)
    await update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
    return States.ACCOUNT_NOTIFS_MENU


async def start_creating_notif(update: Update, _: SnxBotContext) -> str:
    text, keyboard = message_composer.start_creating_notif()
    await update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
    return States.SELECT_NOTIF_TYPE_TO_CREATE


async def request_notif_data(update: Update, context: SnxBotContext) -> str:
    selected_notif_type = NotifType(update.callback_query.data)
    context.chat_data["notif_type"] = selected_notif_type
    if selected_notif_type is not NotifType.ratio:
        return await create_notif(update, context)

    text = message_composer.request_notif_data_with_additional_data(selected_notif_type)
    await update.callback_query.edit_message_text(text=text)
    return States.HANDLE_NOTIF_INFO


async def create_notif(update: Update, context: SnxBotContext) -> str:
    message_delivery: Callable = _get_message_delivery(update)
    notif_type = NotifType(context.chat_data["notif_type"])
    notif_params = {}
    chat_account = await context.get_current_chat_account()

    if notif_type is NotifType.ratio:
        try:
            notif_params = utils.parse_notif_info_message(notif_type, update.message.text)
        except (ValueError, KeyError, IndexError):
            await update.effective_chat.send_message(text="Incorrect data, try again")
            return States.HANDLE_NOTIF_INFO

    exists, notif = await context.create_notif(notif_type, notif_params, chat_account)

    if exists:
        text, keyboard = message_composer.create_notif_already_exists(chat_account.account.address)
    else:
        text, keyboard = message_composer.create_notif(chat_account.account.address)

    await message_delivery(text=text, reply_markup=keyboard)
    return States.NOTIF_CREATED


async def delete_notif(update: Update, context: SnxBotContext) -> str:
    notif_id = UUID(update.callback_query.data)
    await context.delete_notif_by_id(notif_id)
    return await account_notifs_menu(update, context)


async def info(update: Update, _: SnxBotContext):
    text = message_composer.info()
    await update.effective_chat.send_message(text, parse_mode="MarkdownV2")


async def payday(update: Update, context: SnxBotContext):
    text = message_composer.payday(context.snx_data)
    await update.effective_chat.send_message(text)
