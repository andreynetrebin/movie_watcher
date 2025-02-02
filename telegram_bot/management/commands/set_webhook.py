# telegram_bot/management/commands/set_webhook.py
from django.core.management.base import BaseCommand
import requests
from decouple import config

class Command(BaseCommand):
    help = 'Устанавливает вебхук для Telegram-бота'

    def handle(self, *args, **kwargs):
        webhook_url = f"{config('SITE_URL')}/telegram_bot/webhook/"  # Замените на ваш URL
        response = requests.get(f"https://api.telegram.org/bot{config('TELEGRAM_BOT_TOKEN')}/setWebhook?url={webhook_url}")
        print(response.json())