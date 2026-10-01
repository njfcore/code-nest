import uuid
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from .models import Payment, Subscription


def has_active_pro_subscription(user):
    if not user.is_authenticated:
        return False

    return user.subscriptions.filter(
        expires_at__gt=timezone.now()
    ).exists()


def can_access_post(user, post):
    if not post.is_pro:
        return True

    return has_active_pro_subscription(user)

def can_purchase_subscription(user):
    if not user.is_authenticated:
        return False

    return not has_active_pro_subscription(user)

@transaction.atomic
def create_mock_payment(user, plan):
    if not can_purchase_subscription(user):
        raise ValueError(
            'User already has an active Pro subscription.'
        )

    payment = Payment.objects.create(
        user=user,
        plan=plan,
        amount=plan.price,
        transaction_id=uuid.uuid4().hex,
        status='pending',
    )

    return payment


@transaction.atomic
def complete_mock_payment(payment):
    if payment.status == 'paid':
        return payment

    if payment.status != 'pending':
        raise ValueError(
            'Only pending payments can be completed.'
        )

    now = timezone.now()

    payment.status = 'paid'
    payment.paid_at = now
    payment.save(
        update_fields=[
            'status',
            'paid_at',
        ]
    )

    Subscription.objects.create(
        user=payment.user,
        plan=payment.plan,
        started_at=now,
        expires_at=now + timedelta(
            days=payment.plan.duration_days
        ),
    )

    return payment