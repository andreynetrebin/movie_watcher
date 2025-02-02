# telegram_bot/telegram_bot.py
import logging
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackContext
from telegram.ext import filters  # Измените импорт на filters
from django.contrib.auth import get_user_model
from account.models import Profile
from decouple import config

User = get_user_model()

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Словарь для хранения временных данных о пользователях
user_data = {}

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Привет! Используйте команду /connect для связывания вашего аккаунта.')

def connect(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Пожалуйста, введите ваш email для связывания аккаунта:')
    user_data[update.message.from_user.id] = {}  # Инициализируем словарь для хранения данных пользователя

def handle_email(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    email = update.message.text

    try:
        user = User.objects.get(email=email)  # Проверяем, существует ли пользователь с таким email
        profile = user.profile
        profile.telegram_connected = True
        profile.telegram_user_id = str(user_id)  # Сохраняем Telegram ID
        profile.save()

        update.message.reply_text('Ваш аккаунт успешно связан с Telegram!')
    except User.DoesNotExist:
        update.message.reply_text('Такого email нет в базе данных. Пожалуйста, пройдите регистрацию по ссылке.')

def handle_update(update):
    # Обработка входящего обновления
    dispatcher = Updater(token=config('TELEGRAM_BOT_TOKEN'), use_context=True).dispatcher
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("connect", connect))
    dispatcher.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_email))  # Обработка текстовых сообщений

    dispatcher.process_update(Update.de_json(update, None))