from django.conf import settings

from django.contrib import admin

from .views import  *

from django.urls import path

app_name = "accounts"

urlpatterns = [

    path('logout/', logout_view, name= 'logout'),

    path('login/', login_view, name= 'login'),

    path('register/', register_view, name= 'register'),

    path('profile/', profile_view, name= 'profile'),

    path('register/verify/', register_verify_view, name='register_verify'),

    path('register/resend/', register_resend_view, name='register_resend'),

]