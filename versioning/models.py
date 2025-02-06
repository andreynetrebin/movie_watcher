# versioning/models.py
from django.db import models

class Version(models.Model):
    version_number = models.CharField(max_length=10)
    release_date = models.DateField()
    changes = models.TextField()

    def __str__(self):
        return self.version_number