from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = [("admin", "Admin"), ("editor", "Editor")]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="editor")
    bio = models.TextField(blank=True)

    def is_admin(self):
        return self.role == "admin" or self.is_superuser

    def __str__(self):
        return self.email or self.username
