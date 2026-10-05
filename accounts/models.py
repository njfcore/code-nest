from django.contrib.auth import get_user_model
from django.db import models


User = get_user_model()


class UserProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
    )

    phone_number = models.CharField(
        max_length=15,
        unique=True,
    )

    phone_verified = models.BooleanField(
        default=False,
    )

    def __str__(self):
        return self.user.username

class PhoneVerification(models.Model):
    REGISTER = 'register'
    LOGIN = 'login'
    PASSWORD_RESET = 'password_reset'

    PURPOSE_CHOICES = [
        (REGISTER, 'Register'),
        (LOGIN, 'Login'),
        (PASSWORD_RESET, 'Password Reset'),
    ]

    phone_number = models.CharField(
        max_length=15,
    )

    code = models.CharField(
        max_length=6,
    )

    purpose = models.CharField(
        max_length=20,
        choices=PURPOSE_CHOICES,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    expires_at = models.DateTimeField()

    attempts = models.PositiveSmallIntegerField(
        default=0,
    )

    is_used = models.BooleanField(
        default=False,
    )

    def __str__(self):
        return f'{self.phone_number} - {self.purpose}'    