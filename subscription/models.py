from django.conf import settings
from django.db import models


class Plan(models.Model):
    name = models.CharField(max_length=100)
    duration_days = models.PositiveIntegerField()
    price = models.PositiveIntegerField()
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['duration_days']

    def __str__(self):
        return f"{self.name} - {self.price:,} $"


class Subscription(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='subscriptions',
    )
    plan = models.ForeignKey(
        Plan,
        on_delete=models.PROTECT,
        related_name='subscriptions',
        null=True,
        blank=True,
    )
    started_at = models.DateTimeField()
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def is_active(self):
        from django.utils import timezone

        return self.expires_at > timezone.now()

    def __str__(self):
        plan_name = self.plan.name if self.plan else 'No plan'
        return f"{self.user.username} - {plan_name}"


class Payment(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='payments',
    )
    plan = models.ForeignKey(
        Plan,
        on_delete=models.PROTECT,
        related_name='payments',
    )
    amount = models.PositiveIntegerField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
    )

    transaction_id = models.CharField(
        max_length=100,
        unique=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    bank_tracking_code = models.CharField(
        max_length=64,
        unique=True,
        null=True,
        blank=True,
    )
    ref_id = models.CharField(
        max_length=100,
        blank=True,
        default='',
    )
    subscription = models.OneToOneField(
        Subscription,
        on_delete=models.SET_NULL,
        related_name='payment',
        null=True,
        blank=True,
    )

    def __str__(self):
        return f"{self.user.username} - {self.amount:,} $ - {self.status}"