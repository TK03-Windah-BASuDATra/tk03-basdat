from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = [
        ("admin", "Admin"),
        ("organizer", "Organizer"),
        ("customer", "Customer"),
    ]

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default="customer"
    )

    phone_number = models.CharField(max_length=20, blank=True, null=True)

    def is_admin(self):
        return self.role == "admin" or self.is_superuser

    def is_organizer(self):
        return self.role == "organizer"

    def is_customer(self):
        return self.role == "customer"