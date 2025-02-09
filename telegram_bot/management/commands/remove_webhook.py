# telegram_bot/management/commands/remove_webhook.py
from django.core.management.base import BaseCommand
import requests
from decouple import config
class Command(BaseCommand):
    help = 'Устанавливает вебхук для Telegram-бота'
    def handle(self, *args, **kwargs):
        url = f'https://api.telegram.org/bot{config("TELEGRAM_BOT_TOKEN")}/deleteWebhook'
        response = requests.post(url)
        print(response.json())  # Выводит ответ от Telegram