from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm


class RegisterForm(UserCreationForm):
    phone_number = forms.CharField(
        max_length=15,
        label='Phone number',
        widget=forms.TextInput(
            attrs={
                'placeholder': '09xxxxxxxxx',
                'autocomplete': 'tel',
            }
        ),
    )

    class Meta:
        model = User
        fields = (
            'username',
            'phone_number',
            'password1',
            'password2',
        )

    def clean_phone_number(self):
        phone_number = self.cleaned_data['phone_number'].strip()

        if not phone_number.isdigit():
            raise forms.ValidationError(
                'Phone number must contain only digits.'
            )

        if len(phone_number) != 11 or not phone_number.startswith('09'):
            raise forms.ValidationError(
                'Enter a valid Iranian phone number.'
            )

        from .models import UserProfile

        if UserProfile.objects.filter(
            phone_number=phone_number
        ).exists():
            raise forms.ValidationError(
                'This phone number is already registered.'
            )

        return phone_number

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError(
                'This username is already taken.'
            )
        return username

class PhoneLoginForm(forms.Form):
    phone_number = forms.CharField(
        max_length=15,
        label='Phone number',
        widget=forms.TextInput(
            attrs={
                'placeholder': '09xxxxxxxxx',
                'autocomplete': 'tel',
                'inputmode': 'numeric',
            }
        ),
    )

    def clean_phone_number(self):
        phone_number = self.cleaned_data['phone_number'].strip()

        if not phone_number.isdigit():
            raise forms.ValidationError(
                'Phone number must contain only digits.'
            )

        if len(phone_number) != 11 or not phone_number.startswith('09'):
            raise forms.ValidationError(
                'Enter a valid Iranian phone number.'
            )

        from .services import get_user_by_phone

        if get_user_by_phone(phone_number) is None:
            raise forms.ValidationError(
                'No account is associated with this phone number.'
            )

        return phone_number


class PhoneOTPForm(forms.Form):
    code = forms.CharField(
        max_length=6,
        min_length=6,
        label='Verification code',
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Enter 6-digit code',
                'inputmode': 'numeric',
                'autocomplete': 'one-time-code',
                'maxlength': '6',
                'pattern': '[0-9]{6}',
                'autofocus': True,
            }
        ),
    )

    def clean_code(self):
        code = self.cleaned_data['code'].strip()

        if not code.isdigit():
            raise forms.ValidationError(
                'Verification code must be 6 digits.'
            )

        return code    