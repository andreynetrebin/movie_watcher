# telegram_bot/views.py
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from telegram import Update
from .telegram_bot import handle_update  # Импортируйте вашу функцию обработки обновлений

@csrf_exempt
async def telegram_webhook(request):
    if request.method == 'POST':
        update = json.loads(request.body)
        await handle_update(Update.de_json(update, None))  # Обработка обновления
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'error'}, status=400)