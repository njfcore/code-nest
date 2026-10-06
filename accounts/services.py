import secrets
from datetime import timedelta

from django.utils import timezone
from django.contrib.auth import get_user_model

from .models import PhoneVerification, UserProfile


OTP_EXPIRATION_MINUTES = 5
OTP_MAX_ATTEMPTS = 5


def generate_otp():
    return f'{secrets.randbelow(1_000_000):06d}'


def send_otp(verification):
    print(
        '\n'
        '========================================\n'
        '             CODE NEST OTP\n'
        '========================================\n'
        f'Phone   : {verification.phone_number}\n'
        f'Purpose : {verification.get_purpose_display()}\n'
        f'OTP     : {verification.code}\n'
        f'Expires : {verification.expires_at}\n'
        '========================================\n'
    )


def create_otp(phone_number, purpose):
    # Rate limit: 1 OTP per 60 seconds
    recent = PhoneVerification.objects.filter(
        phone_number=phone_number,
        purpose=purpose,
        created_at__gte=timezone.now() - timedelta(seconds=60),
    ).exists()

    if recent:
        raise ValueError(
            'Please wait 60 seconds before requesting a new code.'
        )

    # Invalidate all previous active OTPs for this purpose
    PhoneVerification.objects.filter(
        phone_number=phone_number,
        purpose=purpose,
        is_used=False,
    ).update(is_used=True)

    code = generate_otp()

    expires_at = timezone.now() + timedelta(
        minutes=OTP_EXPIRATION_MINUTES
    )

    verification = PhoneVerification.objects.create(
        phone_number=phone_number,
        code=code,
        purpose=purpose,
        expires_at=expires_at,
    )

    send_otp(verification)

    return verification


def verify_otp(
    phone_number,
    code,
    purpose,
    verification_id=None,
):
    queryset = PhoneVerification.objects.filter(
        phone_number=phone_number,
        purpose=purpose,
        is_used=False,
    )

    if verification_id is not None:
        queryset = queryset.filter(id=verification_id)

    verification = queryset.order_by('-created_at').first()

    if verification is None:
        return False

    if verification.expires_at <= timezone.now():
        verification.is_used = True
        verification.save(update_fields=['is_used'])
        return False

    if verification.attempts >= OTP_MAX_ATTEMPTS:
        verification.is_used = True
        verification.save(update_fields=['is_used'])
        return False

    verification.attempts += 1

    if verification.code != code:
        verification.save(update_fields=['attempts'])
        return False

    verification.is_used = True
    verification.save(update_fields=['attempts', 'is_used'])

    return True

def get_user_by_phone(phone_number):
    """
    Return the user associated with the given phone number,
    or None if no profile exists for that phone.
    """

    User = get_user_model()

    profile = UserProfile.objects.filter(
        phone_number=phone_number,
        phone_verified=True,
    ).select_related('user').first()

    if profile is None:
        return None

    return profile.user