from django.shortcuts import render
from django.core.paginator import Paginator
from .models import Version

def changelog(request):
    versions_list = Version.objects.all().order_by('-release_date')
    paginator = Paginator(versions_list, 10)  # Показывать 10 версий на странице

    page_number = request.GET.get('page')  # Получаем номер страницы из GET-запроса
    versions = paginator.get_page(page_number)  # Получаем версии для текущей страницы

    return render(request, 'versioning/changelog.html', {'versions': versions})
