# telegram_bot/views.py
import json
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from telegram import Update
from asgiref.sync import async_to_sync
from .telegram_bot import application
logger = logging.getLogger(__name__)
@csrf_exempt
def telegram_webhook(request):
    if request.method == 'POST':
        update = json.loads(request.body)
        logger.info(f"Before try section Received update: {update}")
        try:
            update = json.loads(request.body)
            logger.info(f"Received update: {update}")
            async_to_sync(application.process_update)(Update.de_json(update, None))
            return JsonResponse({'status': 'ok'})
        except Exception as e:
            logger.error(f"Error processing update: {e}")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    return JsonResponse({'status': 'error'}, status=400)