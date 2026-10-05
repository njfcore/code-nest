from django.contrib import admin

from .models import UserProfile, PhoneVerification


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'phone_number',
        'phone_verified',
    )
    list_filter = (
        'phone_verified',
    )
    search_fields = (
        'user__username',
        'phone_number',
    )

@admin.register(PhoneVerification)
class PhoneVerificationAdmin(admin.ModelAdmin):
    list_display = (
        'phone_number',
        'purpose',
        'code',
        'created_at',
        'expires_at',
        'attempts',
        'is_used',
    )
    list_filter = (
        'purpose',
        'is_used',
    )
    search_fields = (
        'phone_number',
        'code',
    )
    readonly_fields = (
        'created_at',
    )
    ordering = (
        '-created_at',
    )    