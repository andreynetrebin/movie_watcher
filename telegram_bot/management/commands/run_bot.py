# telegram_bot/management/commands/run_bot.py
from django.core.management.base import BaseCommand
from telegram_bot.telegram_bot import run_bot  # Импортируйте вашу функцию запуска бота

class Command(BaseCommand):
    help = 'Запускает Telegram-бота'

    def handle(self, *args, **kwargs):
        run_bot()