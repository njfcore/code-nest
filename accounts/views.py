from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.decorators import login_required
from django.utils import timezone


def login_view(request):

    if request.user.is_authenticated:
        return redirect('/')

    form = AuthenticationForm(
        request=request,
        data=request.POST or None
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
        'form': form
    }

    return render(request, 'accounts/login.html', context)


@login_required
def logout_view(request):

    logout(request)

    return redirect('/')


def register_view(request):

    if request.user.is_authenticated:
        return redirect('/')

    form = UserCreationForm(
        request.POST or None
    )

    if request.method == 'POST' and form.is_valid():

        form.save()

        return redirect('/accounts/login/')

    context = {
        'form': form
    }

    return render(request, 'accounts/register.html', context)

@login_required
def profile_view(request):

    active_subscription = request.user.subscriptions.filter(
        expires_at__gt=timezone.now()
    ).select_related('plan').order_by('-expires_at').first()

    context = {
        'active_subscription': active_subscription,
        'is_pro': active_subscription is not None,
    }

    return render(
        request,
        'accounts/profile.html',
        context,
    )