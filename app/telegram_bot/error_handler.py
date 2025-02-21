import logging

from telegram import Update
from telegram import error as tg_error
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Note:
    'telegram.error.BadRequest: Not enough rights to send text messages to the chat' -
        common error on telegram end. Ignore it while it is not common.
    """
    error = context.error
    if isinstance(error, tg_error.NetworkError):
        if "Bad Gateway" in str(error) or "httpx.ReadError" in str(error):
            pass
    elif isinstance(error, tg_error.TimedOut) and "Timed out" in str(error):
        pass
    elif isinstance(error, tg_error.TelegramError):
        logger.exception("Unexpected Telegram error: ", exc_info=error)
    else:
        if isinstance(update, Update):
            text = "An unknown error occurred. Please try /start and then repeat your command."
            await update.effective_chat.send_message(text)
            logger.exception("Unexpected error while handling update: ", exc_info=error)
        else:
            logger.exception("Unexpected error: ", exc_info=error)
