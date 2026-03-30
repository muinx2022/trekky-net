from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User, UserSessionAudit


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        ("Trekky", {"fields": ("role", "bio", "avatar", "is_seeded", "google_sub")}),
    )
    list_display = ("email", "username", "role", "is_staff", "is_active")
    list_filter = ("role", "is_staff", "is_active")
    search_fields = ("email", "username")
    ordering = ("email",)


@admin.register(UserSessionAudit)
class UserSessionAuditAdmin(admin.ModelAdmin):
    list_display = ("user", "ip_address", "created_at")
    search_fields = ("user__email", "ip_address")

# Register your models here.
