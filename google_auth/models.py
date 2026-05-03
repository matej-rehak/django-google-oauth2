from django.db import models
from django.contrib.auth.models import User


class GoogleProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='google_profile')
    google_id = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=200)
    email = models.EmailField()
    picture = models.URLField(max_length=500)

    def __str__(self):
        return self.name
