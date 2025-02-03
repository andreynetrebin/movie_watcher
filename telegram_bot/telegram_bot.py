# telegram_bot/telegram_bot.py
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackContext
from asgiref.sync import sync_to_async
from django.contrib.auth import get_user_model
from account.models import Profile
from decouple import config

User = get_user_model()

# Настройка логирования
logger = logging.getLogger(__name__)

# Словарь для хранения временных данных о пользователях
user_data = {}

async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text('Привет! Используйте команду /connect для связывания вашего аккаунта.')

async def connect(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text('Пожалуйста, введите ваш email для связывания аккаунта:')
    user_data[update.message.from_user.id] = {}  # Инициализируем словарь для хранения данных пользователя


async def handle_email(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    email = update.message.text

    try:
        # Получаем пользователя асинхронно
        user = await sync_to_async(User.objects.get)(email=email)  # Проверяем, существует ли пользователь с таким email

        # Получаем профиль асинхронно
        profile = await sync_to_async(lambda: user.profile)()  # Получаем профиль асинхронно
        profile.telegram_connected = True
        profile.telegram_user_id = str(user_id)  # Сохраняем Telegram ID

        # Сохраняем профиль асинхронно
        await sync_to_async(profile.save)()

        await update.message.reply_text('Ваш аккаунт успешно связан с Telegram!')
    except User.DoesNotExist:
        await update.message.reply_text('Такого email нет в базе данных. Пожалуйста, пройдите регистрацию по ссылке.')

async def handle_update(update: Update):
    # Обработка входящего обновления
    await context.bot.process_update(update)

def run_bot():

    application = ApplicationBuilder().token(config('TELEGRAM_BOT_TOKEN')).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("connect", connect))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_email))  # Обработка текстовых сообщений
    # Настройка вебхука
    application.run_webhook(
        listen='0.0.0.0',  # Слушаем на всех интерфейсах
        port=int(config('PORT', default=8443)),  # Порт, на котором будет работать вебхук
        url_path=config('TELEGRAM_BOT_TOKEN'),  # URL путь для вебхука
        webhook_url=f'{config("SITE_URL")}/telegram_bot/'  # Замените <your_public_url> на ваш публичный URL
    )