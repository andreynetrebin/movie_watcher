# versioning/context_processors.py
from .models import Version

def current_version(request):
    try:
        version = Version.objects.last()  # Получаем последнюю версию
        return {'current_version': version}
    except Version.DoesNotExist:
        return {'current_version': None}