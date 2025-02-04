import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackContext
from asgiref.sync import sync_to_async
from django.contrib.auth import get_user_model
from account.models import Profile
from decouple import config
User  = get_user_model()
logger = logging.getLogger(__name__)
user_data = {}
# Создайте глобальный экземпляр приложения
application = ApplicationBuilder().token(config('TELEGRAM_BOT_TOKEN')).build()
async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text('Привет! Используйте команду /connect для связывания вашего аккаунта.')
async def connect(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text('Пожалуйста, введите ваш email для связывания аккаунта:')
    user_data[update.message.from_user.id] = {}
async def handle_email(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    email = update.message.text
    try:
        user = await sync_to_async(User.objects.get)(email=email)
        profile = await sync_to_async(lambda: user.profile)()
        profile.telegram_connected = True
        profile.telegram_user_id = str(user_id)
        await sync_to_async(profile.save)()
        await update.message.reply_text('Ваш аккаунт успешно связан с Telegram!')
    except User.DoesNotExist:
        await update.message.reply_text('Такого email нет в базе данных. Пожалуйста, пройдите регистрацию')
def run_bot():
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("connect", connect))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_email))
    # Запуск опроса
    application.run_polling()