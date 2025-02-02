import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from telegram import Update
from telegram.ext import Dispatcher
from telegram_bot import telegram_bot  # Импортируйте ваш файл с логикой бота

@csrf_exempt
def telegram_webhook(request):
    if request.method == 'POST':
        update = json.loads(request.body)
        telegram_bot.handle_update(update)  # Обработка обновления
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'error'}, status=400)