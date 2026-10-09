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

    path('change-password/', change_password_view, name='change_password'),

    path('change-password/verify/' ,change_password_verify_view, name='change_password_verify'),

    path('change-password/resend/', change_password_resend_view, name='change_password_resend'),

    path('edit-profile/', edit_profile_view, name='edit_profile'),

    path('edit-profile/verify/', edit_profile_verify_view, name='edit_profile_verify'),

    path('edit-profile/resend/', edit_profile_resend_view, name='edit_profile_resend'),

]