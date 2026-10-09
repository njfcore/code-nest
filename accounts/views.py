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

from .forms import RegisterForm, PhoneLoginForm, PhoneOTPForm, ChangePasswordForm, EditProfileForm
from .models import PhoneVerification, UserProfile
from .services import create_otp, verify_otp, get_user_by_phone


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

def login_otp_view(request):
    """
    Step 1 of OTP login: ask for the phone number.
    """

    if request.user.is_authenticated:
        return redirect('/')

    form = PhoneLoginForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():

        phone_number = form.cleaned_data['phone_number']

        try:
            verification = create_otp(
                phone_number,
                PhoneVerification.LOGIN,
            )
        except ValueError as error:
            form.add_error(None, str(error))
            return render(
                request,
                'accounts/login_otp.html',
                {'form': form},
            )

        request.session['login_otp_phone'] = phone_number
        request.session['login_otp_verification_id'] = verification.id
        request.session.set_expiry(600)  # 10 minutes

        return redirect('/accounts/login/otp/verify/')

    return render(
        request,
        'accounts/login_otp.html',
        {'form': form},
    )


def login_otp_verify_view(request):
    """
    Step 2 of OTP login: verify the code and log the user in.
    """

    if request.user.is_authenticated:
        return redirect('/')

    phone_number = request.session.get('login_otp_phone')
    verification_id = request.session.get('login_otp_verification_id')

    if not phone_number or not verification_id:
        return redirect('/accounts/login/otp/')

    resend_error = request.session.pop('login_otp_resend_error', None)
    resend_success = request.session.pop('login_otp_resend_success', None)

    form = PhoneOTPForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():

        code = form.cleaned_data['code']

        if verify_otp(
            phone_number,
            code,
            PhoneVerification.LOGIN,
            verification_id=verification_id,
        ):
            user = get_user_by_phone(phone_number)

            request.session.pop('login_otp_phone', None)
            request.session.pop('login_otp_verification_id', None)

            if user is None:
                messages.error(
                    request,
                    'No account is associated with this phone number.'
                )
                return redirect('/accounts/login/otp/')

            login(request, user)

            messages.success(
                request,
                f'Welcome back, {user.username}!'
            )

            return redirect('/')

        form.add_error(
            'code',
            'Invalid or expired verification code.',
        )

    context = {
        'form': form,
        'phone_number': phone_number,
        'resend_error': resend_error,
        'resend_success': resend_success,
    }

    return render(
        request,
        'accounts/login_otp_verify.html',
        context,
    )


def login_otp_resend_view(request):
    """
    Resend the OTP for the login flow (Post/Redirect/Get).
    """

    if request.user.is_authenticated:
        return redirect('/')

    phone_number = request.session.get('login_otp_phone')

    if not phone_number:
        return redirect('/accounts/login/otp/')

    try:
        verification = create_otp(
            phone_number,
            PhoneVerification.LOGIN,
        )
    except ValueError as error:
        request.session['login_otp_resend_error'] = str(error)
        return redirect('/accounts/login/otp/verify/')

    request.session['login_otp_verification_id'] = verification.id
    request.session['login_otp_resend_success'] = (
        'A new verification code has been sent to your phone.'
    )

    return redirect('/accounts/login/otp/verify/')

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

# =========================================
# Change Password Flow
# =========================================

@login_required
def change_password_view(request):
    """
    Step 1: send OTP to the user's registered phone number.
    """

    user_profile = getattr(request.user, 'profile', None)

    if not user_profile or not user_profile.phone_number:
        messages.error(
            request,
            'You need a verified phone number to change your password. '
            'Please add one in your profile first.'
        )
        return redirect('/accounts/profile/')

    if not user_profile.phone_verified:
        messages.error(
            request,
            'Your phone number is not verified yet. '
            'Please verify it first.'
        )
        return redirect('/accounts/profile/')

    # Already sent an OTP? Show the verify page.
    if request.session.get('change_password_verification_id'):
        return redirect('/accounts/change-password/verify/')

    try:
        verification = create_otp(
            user_profile.phone_number,
            PhoneVerification.PASSWORD_RESET,
        )
    except ValueError as error:
        messages.error(request, str(error))
        return redirect('/accounts/profile/')

    request.session['change_password_verification_id'] = verification.id
    request.session['change_password_phone'] = user_profile.phone_number
    request.session.set_expiry(600)

    return redirect('/accounts/change-password/verify/')


@login_required
def change_password_verify_view(request):
    """
    Step 2: verify OTP and set the new password.
    """

    verification_id = request.session.get('change_password_verification_id')
    phone_number = request.session.get('change_password_phone')

    if not verification_id or not phone_number:
        return redirect('/accounts/change-password/')

    resend_error = request.session.pop('change_password_resend_error', None)
    resend_success = request.session.pop('change_password_resend_success', None)

    otp_form = PhoneOTPForm(request.POST or None, prefix='otp')
    password_form = ChangePasswordForm(request.POST or None, prefix='pw')

    if request.method == 'POST':

        if otp_form.is_valid() and password_form.is_valid():

            code = otp_form.cleaned_data['code']

            if verify_otp(
                phone_number,
                code,
                PhoneVerification.PASSWORD_RESET,
                verification_id=verification_id,
            ):
                request.user.set_password(
                    password_form.cleaned_data['new_password1']
                )
                request.user.save()

                # Clear the session
                request.session.pop('change_password_verification_id', None)
                request.session.pop('change_password_phone', None)

                messages.success(
                    request,
                    'Your password has been changed successfully. '
                    'Please log in again.'
                )

                # Force re-login because the password changed
                logout(request)
                return redirect('/accounts/login/')

            otp_form.add_error(
                'code',
                'Invalid or expired verification code.',
            )

    context = {
        'otp_form': otp_form,
        'password_form': password_form,
        'phone_number': phone_number,
        'resend_error': resend_error,
        'resend_success': resend_success,
    }

    return render(
        request,
        'accounts/change_password_verify.html',
        context,
    )


@login_required
def change_password_resend_view(request):
    """
    Resend the OTP for the change password flow.
    """

    phone_number = request.session.get('change_password_phone')

    if not phone_number:
        return redirect('/accounts/change-password/')

    try:
        verification = create_otp(
            phone_number,
            PhoneVerification.PASSWORD_RESET,
        )
    except ValueError as error:
        request.session['change_password_resend_error'] = str(error)
        return redirect('/accounts/change-password/verify/')

    request.session['change_password_verification_id'] = verification.id
    request.session['change_password_resend_success'] = (
        'A new verification code has been sent to your phone.'
    )

    return redirect('/accounts/change-password/verify/')


# =========================================
# Edit Profile Flow
# =========================================

@login_required
def edit_profile_view(request):
    """
    Edit username and phone number.

    Phone change flow:
    - If the user has no verified phone yet:
        * Send OTP to the new phone (single-step verification).
    - If the user already has a verified phone and wants to change it:
        * First send OTP to the OLD phone (prove identity).
        * Then send OTP to the NEW phone (prove ownership).
    """

    user_profile = getattr(request.user, 'profile', None)

    # Create profile if missing (edge case for legacy users)
    if user_profile is None:
        user_profile = UserProfile.objects.create(
            user=request.user,
            phone_number='',
        )

    current_phone = user_profile.phone_number or ''
    has_verified_phone = bool(
        current_phone and user_profile.phone_verified
    )

    form = EditProfileForm(
        request.POST or None,
        user=request.user,
        initial={
            'username': request.user.username,
            'phone_number': current_phone,
        },
    )

    if request.method == 'POST' and form.is_valid():

        new_username = form.cleaned_data['username']
        new_phone = form.cleaned_data['phone_number']

        # -------------------------------------------------
        # Case 1: phone number unchanged
        # -------------------------------------------------
        if new_phone == current_phone:

            request.user.username = new_username
            request.user.save(update_fields=['username'])

            messages.success(
                request,
                'Your profile has been updated.'
            )
            return redirect('/accounts/profile/')

        # -------------------------------------------------
        # Case 2: user has no verified phone yet
        #         ? single-step OTP to the NEW phone
        # -------------------------------------------------
        if not has_verified_phone:

            try:
                verification = create_otp(
                    new_phone,
                    PhoneVerification.REGISTER,
                )
            except ValueError as error:
                form.add_error(None, str(error))
                return render(
                    request,
                    'accounts/edit_profile.html',
                    {'form': form},
                )

            # Clear any previous state
            _clear_edit_profile_session(request)

            request.session['edit_profile_flow'] = 'new_phone_only'
            request.session['edit_profile_verification_id'] = verification.id
            request.session['edit_profile_new_phone'] = new_phone
            request.session['edit_profile_new_username'] = new_username
            request.session.set_expiry(600)

            return redirect('/accounts/edit-profile/verify/')

        # -------------------------------------------------
        # Case 3: user has verified phone, changing it
        #         ? first OTP to the OLD phone
        # -------------------------------------------------
        try:
            verification = create_otp(
                current_phone,
                PhoneVerification.PASSWORD_RESET,
                # purpose reuse — we just need a fresh OTP
            )
        except ValueError as error:
            form.add_error(None, str(error))
            return render(
                request,
                'accounts/edit_profile.html',
                {'form': form},
            )

        _clear_edit_profile_session(request)

        request.session['edit_profile_flow'] = 'verify_old_phone'
        request.session['edit_profile_verification_id'] = verification.id
        request.session['edit_profile_old_phone'] = current_phone
        request.session['edit_profile_new_phone'] = new_phone
        request.session['edit_profile_new_username'] = new_username
        request.session.set_expiry(600)

        return redirect('/accounts/edit-profile/verify/')

    context = {
        'form': form,
    }

    return render(
        request,
        'accounts/edit_profile.html',
        context,
    )


def _clear_edit_profile_session(request):
    """Helper to clear all edit-profile session keys."""
    keys = (
        'edit_profile_flow',
        'edit_profile_verification_id',
        'edit_profile_old_phone',
        'edit_profile_new_phone',
        'edit_profile_new_username',
        'edit_profile_resend_error',
        'edit_profile_resend_success',
    )
    for key in keys:
        request.session.pop(key, None)


@login_required
def edit_profile_verify_view(request):
    """
    Handle OTP verification for both stages of the edit profile flow.
    """

    flow = request.session.get('edit_profile_flow')
    verification_id = request.session.get('edit_profile_verification_id')
    old_phone = request.session.get('edit_profile_old_phone')
    new_phone = request.session.get('edit_profile_new_phone')
    new_username = request.session.get('edit_profile_new_username')

    if not flow or not verification_id or not new_phone or not new_username:
        return redirect('/accounts/edit-profile/')

    # Decide which phone to verify at this step
    if flow == 'verify_old_phone':
        phone_to_verify = old_phone
        otp_purpose = PhoneVerification.PASSWORD_RESET
    else:
        phone_to_verify = new_phone
        otp_purpose = PhoneVerification.REGISTER

    resend_error = request.session.pop('edit_profile_resend_error', None)
    resend_success = request.session.pop('edit_profile_resend_success', None)

    form = PhoneOTPForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():

        code = form.cleaned_data['code']

        if verify_otp(
            phone_to_verify,
            code,
            otp_purpose,
            verification_id=verification_id,
        ):
            # ---------------------------------------------
            # Stage 1 done: old phone verified
            # Now send OTP to the new phone
            # ---------------------------------------------
            if flow == 'verify_old_phone':

                try:
                    verification = create_otp(
                        new_phone,
                        PhoneVerification.REGISTER,
                    )
                except ValueError as error:
                    messages.error(request, str(error))
                    _clear_edit_profile_session(request)
                    return redirect('/accounts/edit-profile/')

                request.session['edit_profile_flow'] = 'verify_new_phone'
                request.session['edit_profile_verification_id'] = verification.id
                request.session['edit_profile_resend_success'] = (
                    'Phone verified. '
                    'A new code has been sent to your new number.'
                )

                return redirect('/accounts/edit-profile/verify/')

            # ---------------------------------------------
            # Stage 2 done: new phone verified
            # Apply changes atomically
            # ---------------------------------------------
            if flow == 'verify_new_phone' or flow == 'new_phone_only':

                user_profile = getattr(request.user, 'profile', None)

                if user_profile is None:
                    _clear_edit_profile_session(request)
                    return redirect('/accounts/edit-profile/')

                try:
                    with transaction.atomic():

                        if User.objects.filter(
                            username=new_username
                        ).exclude(pk=request.user.pk).exists():
                            raise IntegrityError('Username taken.')

                        if UserProfile.objects.filter(
                            phone_number=new_phone
                        ).exclude(user=request.user).exists():
                            raise IntegrityError('Phone taken.')

                        request.user.username = new_username
                        request.user.save(update_fields=['username'])

                        user_profile.phone_number = new_phone
                        user_profile.phone_verified = True
                        user_profile.save(update_fields=[
                            'phone_number',
                            'phone_verified',
                        ])

                except IntegrityError:
                    _clear_edit_profile_session(request)
                    messages.error(
                        request,
                        'This phone number or username is already '
                        'registered. Please try again.'
                    )
                    return redirect('/accounts/edit-profile/')

                _clear_edit_profile_session(request)

                messages.success(
                    request,
                    'Your profile has been updated.'
                )
                return redirect('/accounts/profile/')

        form.add_error(
            'code',
            'Invalid or expired verification code.',
        )

    # Decide which phone number to display in the UI
    if flow == 'verify_old_phone':
        display_phone = old_phone
        stage = 'old'
    else:
        display_phone = new_phone
        stage = 'new'

    context = {
        'form': form,
        'phone_number': display_phone,
        'stage': stage,
        'flow': flow,
        'resend_error': resend_error,
        'resend_success': resend_success,
    }

    return render(
        request,
        'accounts/edit_profile_verify.html',
        context,
    )

@login_required
def edit_profile_resend_view(request):
    """
    Resend OTP for the current stage of the edit profile flow.
    """

    flow = request.session.get('edit_profile_flow')
    old_phone = request.session.get('edit_profile_old_phone')
    new_phone = request.session.get('edit_profile_new_phone')

    if not flow or not new_phone:
        return redirect('/accounts/edit-profile/')

    if flow == 'verify_old_phone':
        phone_to_send = old_phone
        otp_purpose = PhoneVerification.PASSWORD_RESET
    else:
        phone_to_send = new_phone
        otp_purpose = PhoneVerification.REGISTER

    try:
        verification = create_otp(
            phone_to_send,
            otp_purpose,
        )
    except ValueError as error:
        request.session['edit_profile_resend_error'] = str(error)
        return redirect('/accounts/edit-profile/verify/')

    request.session['edit_profile_verification_id'] = verification.id
    request.session['edit_profile_resend_success'] = (
        'A new verification code has been sent to your phone.'
    )

    return redirect('/accounts/edit-profile/verify/')

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
        'profile': getattr(request.user, 'profile', None),
    }

    return render(
        request,
        'accounts/profile.html',
        context,
    )