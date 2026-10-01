from django.urls import path

from . import views


app_name = 'subscription'

urlpatterns = [
    path('', views.plans, name='plans'),
    path('checkout/<int:plan_id>/', views.checkout, name='checkout'),
    path(
        'payment/<int:payment_id>/',
        views.payment,
        name='payment',
    ),
    path(
        'payment/<int:payment_id>/success/',
        views.payment_success,
        name='payment_success',
    ),
]