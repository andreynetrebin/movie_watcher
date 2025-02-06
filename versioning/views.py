# versioning/views.py
from django.shortcuts import render
from .models import Version

def changelog(request):
    versions = Version.objects.all().order_by('-release_date')
    return render(request, 'versioning/changelog.html', {'versions': versions})