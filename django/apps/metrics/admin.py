from django.contrib import admin
from django.utils.html import format_html
from .models import TokenUsageDaily, AuthFailure, SyncLog


@admin.register(TokenUsageDaily)
class TokenUsageDailyAdmin(admin.ModelAdmin):
    list_display = ["token", "date", "request_count", "success_count", "error_count", "bytes_sent"]
    list_filter = ["date"]
    readonly_fields = [f.name for f in TokenUsageDaily._meta.fields]
    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False


@admin.register(AuthFailure)
class AuthFailureAdmin(admin.ModelAdmin):
    list_display = ["timestamp", "failure_reason", "token_prefix", "client_ip", "request_path"]
    list_filter = ["failure_reason"]
    readonly_fields = [f.name for f in AuthFailure._meta.fields]
    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False


@admin.register(SyncLog)
class SyncLogAdmin(admin.ModelAdmin):
    list_display = ["started_at", "source", "status_badge", "keys_added", "keys_updated", "errors_count"]
    list_filter = ["status"]
    readonly_fields = [f.name for f in SyncLog._meta.fields]
    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False

    def status_badge(self, obj):
        colors = {"running": "blue", "success": "green", "partial": "orange", "failed": "red"}
        return format_html('<span style="color:{};">● {}</span>', colors.get(obj.status, "gray"), obj.status)
    status_badge.short_description = "Status"
