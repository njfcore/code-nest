from django.contrib import admin

from .models import Plan, Subscription, Payment


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'duration_days',
        'price',
        'is_active',
        'created_at',
    )
    list_filter = (
        'is_active',
    )
    search_fields = (
        'name',
    )
    ordering = (
        'duration_days',
    )


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'plan',
        'started_at',
        'expires_at',
        'is_active',
        'created_at',
    )
    list_filter = (
        'plan',
        'started_at',
        'expires_at',
    )
    search_fields = (
        'user__username',
        'user__email',
    )
    readonly_fields = (
        'created_at',
    )


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'plan',
        'amount',
        'status',
        'transaction_id',
        'created_at',
        'paid_at',
    )
    list_filter = (
        'status',
        'plan',
        'created_at',
    )
    search_fields = (
        'user__username',
        'user__email',
        'transaction_id',
    )
    readonly_fields = (
        'created_at',
        'paid_at',
    )