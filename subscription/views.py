from azbankgateways import default_settings as bank_settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render

from .models import Payment, Plan
from .services import (
    can_purchase_subscription,
    create_payment,
    finalize_gateway_payment,
    has_active_pro_subscription,
    start_gateway_payment,
)


def plans(request):
    context = {
        'plans': Plan.objects.filter(is_active=True),
        'is_pro': has_active_pro_subscription(request.user),
    }
    return render(request, 'subscription/plans.html', context)


@login_required
def checkout(request, plan_id):
    plan = get_object_or_404(Plan, id=plan_id, is_active=True)

    if not can_purchase_subscription(request.user):
        messages.warning(
            request,
            'You already have an active Pro subscription.',
        )
        return redirect('accounts:profile')

    if request.method == 'POST':
        try:
            payment = create_payment(request.user, plan)
        except ValueError as error:
            messages.error(request, str(error))
            return redirect('subscription:plans')

        return redirect('subscription:payment', payment_id=payment.id)

    return render(request, 'subscription/checkout.html', {'plan': plan})


@login_required
def payment(request, payment_id):
    payment_object = get_object_or_404(
        Payment,
        id=payment_id,
        user=request.user,
    )

    if payment_object.status == 'paid':
        return redirect(
            'subscription:payment_success',
            payment_id=payment_object.id,
        )

    if payment_object.status == 'failed':
        return redirect(
            'subscription:payment_failed',
            payment_id=payment_object.id,
        )

    if request.method == 'POST':
        try:
            return start_gateway_payment(request, payment_object)
        except ValueError as error:
            messages.error(request, str(error))
            return redirect('subscription:plans')

    return render(
        request,
        'subscription/payment.html',
        {'payment': payment_object},
    )


def callback(request):
    tracking_code = request.GET.get(
        bank_settings.TRACKING_CODE_QUERY_PARAM
    )

    if not tracking_code:
        raise Http404

    payment_object = finalize_gateway_payment(tracking_code)

    if payment_object is None:
        raise Http404

    if payment_object.status == 'paid':
        return redirect(
            'subscription:payment_success',
            payment_id=payment_object.id,
        )

    return redirect(
        'subscription:payment_failed',
        payment_id=payment_object.id,
    )


@login_required
def payment_success(request, payment_id):
    payment_object = get_object_or_404(
        Payment.objects.select_related('plan', 'subscription'),
        id=payment_id,
        user=request.user,
        status='paid',
    )

    return render(
        request,
        'subscription/payment_success.html',
        {
            'payment': payment_object,
            'subscription': payment_object.subscription,
        },
    )


@login_required
def payment_failed(request, payment_id):
    payment_object = get_object_or_404(
        Payment,
        id=payment_id,
        user=request.user,
    )

    return render(
        request,
        'subscription/payment_failed.html',
        {'payment': payment_object},
    )