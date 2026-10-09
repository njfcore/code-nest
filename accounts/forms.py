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

class ChangePasswordForm(forms.Form):
    """
    Form for the new password (used after OTP verification).
    """

    new_password1 = forms.CharField(
        label='New password',
        widget=forms.PasswordInput(
            attrs={
                'placeholder': 'Create a strong password',
                'autocomplete': 'new-password',
            }
        ),
    )

    new_password2 = forms.CharField(
        label='Confirm new password',
        widget=forms.PasswordInput(
            attrs={
                'placeholder': 'Repeat your new password',
                'autocomplete': 'new-password',
            }
        ),
    )

    def clean(self):
        cleaned_data = super().clean()

        password1 = cleaned_data.get('new_password1')
        password2 = cleaned_data.get('new_password2')

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(
                'The two password fields must match.'
            )

        if password1 and len(password1) < 8:
            raise forms.ValidationError(
                'Password must be at least 8 characters long.'
            )

        return cleaned_data


class EditProfileForm(forms.Form):
    """
    Form for editing username and phone number.
    """

    username = forms.CharField(
        max_length=150,
        label='Username',
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Choose a username',
                'autocomplete': 'username',
            }
        ),
    )

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

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean_username(self):
        username = self.cleaned_data['username'].strip()

        if User.objects.filter(username=username).exclude(
            pk=self.user.pk
        ).exists():
            raise forms.ValidationError(
                'This username is already taken.'
            )

        return username

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
        ).exclude(user=self.user).exists():
            raise forms.ValidationError(
                'This phone number is already registered.'
            )

        return phone_number    