from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .models import Plan, Payment
from .services import (
    can_purchase_subscription,
    complete_mock_payment,
    create_mock_payment,
    has_active_pro_subscription,
)


def plans(request):
    plans_list = Plan.objects.filter(
        is_active=True
    )

    is_pro = has_active_pro_subscription(request.user)

    context = {
        'plans': plans_list,
        'is_pro': is_pro,
    }

    return render(
        request,
        'subscription/plans.html',
        context,
    )


@login_required
def checkout(request, plan_id):
    plan = get_object_or_404(
        Plan,
        id=plan_id,
        is_active=True,
    )

    if not can_purchase_subscription(request.user):
        messages.warning(
            request,
            'You already have an active Pro subscription.',
        )
        return redirect('accounts:profile')

    if request.method == 'POST':
        try:
            payment = create_mock_payment(
                request.user,
                plan,
            )
        except ValueError as error:
            messages.error(
                request,
                str(error),
            )
            return redirect('subscription:plans')

        return redirect(
            'subscription:payment',
            payment_id=payment.id,
        )

    context = {
        'plan': plan,
    }

    return render(
        request,
        'subscription/checkout.html',
        context,
    )


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

    if request.method == 'POST':
        try:
            complete_mock_payment(payment_object)
        except ValueError as error:
            messages.error(
                request,
                str(error),
            )
            return redirect(
                'subscription:plans'
            )

        return redirect(
            'subscription:payment_success',
            payment_id=payment_object.id,
        )

    context = {
        'payment': payment_object,
    }

    return render(
        request,
        'subscription/payment.html',
        context,
    )


@login_required
def payment_success(request, payment_id):
    payment_object = get_object_or_404(
        Payment,
        id=payment_id,
        user=request.user,
        status='paid',
    )

    subscription = payment_object.user.subscriptions.filter(
        created_at__gte=payment_object.paid_at,
        plan=payment_object.plan,
    ).order_by('-created_at').first()

    context = {
        'payment': payment_object,
        'subscription': subscription,
    }

    return render(
        request,
        'subscription/payment_success.html',
        context,
    )