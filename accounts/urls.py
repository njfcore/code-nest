from django.conf import settings

from django.contrib import admin

from .views import  *

from django.urls import path

app_name = "accounts"

urlpatterns = [

    path('logout/', logout_view, name= 'logout'),

    path('login/', login_view, name= 'login'),

    path('login/otp/', login_otp_view, name='login_otp'),

    path('login/otp/verify/' ,login_otp_verify_view, name='login_otp_verify'),

    path('login/otp/resend/', login_otp_resend_view, name='login_otp_resend'),

    path('register/', register_view, name= 'register'),

    path('profile/', profile_view, name= 'profile'),

    path('register/verify/', register_verify_view, name='register_verify'),

    path('register/resend/', register_resend_view, name='register_resend'),

]