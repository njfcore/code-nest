import uuid
from datetime import timedelta
from decimal import Decimal, InvalidOperation

from azbankgateways import bankfactories
from azbankgateways import models as bank_models
from azbankgateways.exceptions import AZBankGatewaysException
from django.db import transaction
from django.urls import reverse
from django.utils import timezone

from .models import Payment, Subscription

# 1$ = 1000 Toman = 10,000 Rial
RIAL_PER_DOLLAR = 10_000


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
def create_payment(user, plan):
    if not can_purchase_subscription(user):
        raise ValueError(
            'User already has an active Pro subscription.'
        )

    return Payment.objects.create(
        user=user,
        plan=plan,
        amount=plan.price,  # Toman
        transaction_id=uuid.uuid4().hex,
        status='pending',
    )


def start_gateway_payment(request, payment):
    """
    Create a bank record and return a redirect response to the gateway.
    """
    if payment.status != 'pending':
        raise ValueError('Only pending payments can be paid.')

    try:
        factory = bankfactories.BankFactory()
        bank = factory.create(bank_models.BankType.ZARINPAL)
        bank.set_request(request)
        bank.set_amount(payment.amount * RIAL_PER_DOLLAR)
        bank.set_client_callback_url(
            reverse('subscription:callback')
        )

        bank_record = bank.ready()
        response = bank.redirect_gateway()
    except AZBankGatewaysException as error:
        raise ValueError(
            'Could not connect to the payment gateway.'
        ) from error

    payment.bank_tracking_code = bank_record.tracking_code
    payment.save(update_fields=['bank_tracking_code'])

    return response


def _amount_matches(bank_record, payment):
    try:
        bank_amount = int(Decimal(str(bank_record.amount)))
    except (InvalidOperation, ValueError):
        return False

    return bank_amount == payment.amount * RIAL_PER_DOLLAR


@transaction.atomic
def finalize_gateway_payment(tracking_code):
    """
    Called from the callback view. The bank record is already verified
    by the gateway package at this point. Safe to call multiple times.
    """
    payment = (
        Payment.objects
        .select_for_update()
        .select_related('plan', 'user')
        .filter(bank_tracking_code=tracking_code)
        .first()
    )

    if payment is None:
        return None

    if payment.status != 'pending':
        return payment

    bank_record = bank_models.Bank.objects.filter(
        tracking_code=tracking_code
    ).first()

    if (
        bank_record is not None
        and bank_record.is_success
        and _amount_matches(bank_record, payment)
    ):
        _complete_payment(
            payment,
            ref_id=str(bank_record.reference_number or ''),
        )
    else:
        payment.status = 'failed'
        payment.save(update_fields=['status'])

    return payment


def _complete_payment(payment, ref_id=''):
    now = timezone.now()

    subscription = Subscription.objects.create(
        user=payment.user,
        plan=payment.plan,
        started_at=now,
        expires_at=now + timedelta(days=payment.plan.duration_days),
    )

    payment.status = 'paid'
    payment.paid_at = now
    payment.ref_id = ref_id
    payment.subscription = subscription
    payment.save(
        update_fields=['status', 'paid_at', 'ref_id', 'subscription']
    )