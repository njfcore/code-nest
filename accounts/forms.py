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