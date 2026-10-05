from django.contrib.auth import (
    authenticate,
    login,
    logout,
)
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.shortcuts import redirect, render
from django.utils import timezone
from django.db import IntegrityError, transaction
from django.contrib import messages

from .forms import RegisterForm
from .models import PhoneVerification, UserProfile
from .services import create_otp, verify_otp


def login_view(request):

    if request.user.is_authenticated:
        return redirect('/')

    form = AuthenticationForm(
        request=request,
        data=request.POST or None,
    )

    if request.method == 'POST' and form.is_valid():

        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password')

        user = authenticate(
            request,
            username=username,
            password=password,
        )

        if user is not None:
            login(request, user)
            return redirect('/')

    context = {
        'form': form,
    }

    return render(
        request,
        'accounts/login.html',
        context,
    )


@login_required
def logout_view(request):

    logout(request)

    return redirect('/')


def register_view(request):

    if request.user.is_authenticated:
        return redirect('/')

    form = RegisterForm(
        request.POST or None,
    )

    if request.method == 'POST' and form.is_valid():

        phone_number = form.cleaned_data['phone_number']

        try:
            verification = create_otp(
                phone_number,
                PhoneVerification.REGISTER,
            )
        except ValueError as error:

            form.add_error(None, str(error))

            context = {
                'form': form,
            }

            return render(
                request,
                'accounts/register.html',
                context,
            )

        request.session['register_data'] = {
            'username': form.cleaned_data['username'],
            'raw_password': form.cleaned_data['password1'],
            'phone_number': phone_number,
        }

        request.session['register_verification_id'] = verification.id

        # Short session lifetime for the pending registration
        request.session.set_expiry(600)  # 10 minutes

        return redirect('/accounts/register/verify/')

    context = {
        'form': form,
    }

    return render(
        request,
        'accounts/register.html',
        context,
    )


def register_verify_view(request):

    if request.user.is_authenticated:
        return redirect('/')

    register_data = request.session.get('register_data')
    verification_id = request.session.get('register_verification_id')

    if not register_data or not verification_id:
        return redirect('/accounts/register/')

    verification = PhoneVerification.objects.filter(
        id=verification_id,
        phone_number=register_data['phone_number'],
        purpose=PhoneVerification.REGISTER,
        is_used=False,
    ).first()

    if verification is None:
        request.session.pop('register_data', None)
        request.session.pop('register_verification_id', None)
        return redirect('/accounts/register/')

    resend_error = request.session.pop('resend_error', None)
    resend_success = request.session.pop('resend_success', None)

    if request.method == 'POST':

        code = request.POST.get('code', '').strip()

        if verify_otp(
            register_data['phone_number'],
            code,
            PhoneVerification.REGISTER,
            verification_id=verification_id,
        ):
            try:
                with transaction.atomic():

                    if User.objects.filter(
                        username=register_data['username']
                    ).exists():
                        raise IntegrityError('Username already taken.')

                    user = User(username=register_data['username'])
                    user.set_password(register_data['raw_password'])
                    user.save()

                    UserProfile.objects.create(
                        user=user,
                        phone_number=register_data['phone_number'],
                        phone_verified=True,
                    )

            except IntegrityError:

                request.session.pop('register_data', None)
                request.session.pop('register_verification_id', None)

                messages.error(
                    request,
                    'This phone number or username is already '
                    'registered. Please try a different one.'
                )

                return redirect('/accounts/register/')

            request.session.pop('register_data', None)
            request.session.pop('register_verification_id', None)

            messages.success(
                request,
                'Your account has been created. Please log in.'
            )

            return redirect('/accounts/login/')

        context = {
            'error': 'Invalid or expired verification code.',
            'phone_number': register_data['phone_number'],
            'resend_error': resend_error,
            'resend_success': resend_success,
        }
        return render(request, 'accounts/register_verify.html', context)

    context = {
        'phone_number': register_data['phone_number'],
        'resend_error': resend_error,
        'resend_success': resend_success,
    }
    return render(request, 'accounts/register_verify.html', context)


def register_resend_view(request):
    """
    Resend the OTP for a pending registration.
    """

    if request.user.is_authenticated:
        return redirect('/')

    register_data = request.session.get('register_data')

    if not register_data:
        return redirect('/accounts/register/')

    phone_number = register_data['phone_number']

    try:
        verification = create_otp(
            phone_number,
            PhoneVerification.REGISTER,
        )
    except ValueError as error:
        request.session['resend_error'] = str(error)
        return redirect('/accounts/register/verify/')

    request.session['register_verification_id'] = verification.id
    request.session['resend_success'] = (
        'A new verification code has been sent to your phone.'
    )

    return redirect('/accounts/register/verify/')


@login_required
def profile_view(request):

    active_subscription = request.user.subscriptions.filter(
        expires_at__gt=timezone.now()
    ).select_related(
        'plan'
    ).order_by(
        '-expires_at'
    ).first()

    context = {
        'active_subscription': active_subscription,
        'is_pro': active_subscription is not None,
    }

    return render(
        request,
        'accounts/profile.html',
        context,
    )