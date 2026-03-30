from django.contrib import admin, messages
from django.utils.html import format_html
from django.utils import timezone
from .models import Client, ApiToken


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ["name", "email", "is_active", "created_at"]
    list_filter = ["is_active"]
    search_fields = ["name", "email"]
    readonly_fields = ["id", "created_at", "updated_at"]

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user.email
        super().save_model(request, obj, form, change)


@admin.register(ApiToken)
class ApiTokenAdmin(admin.ModelAdmin):
    list_display = ["name", "client", "token_prefix", "status_badge", "expires_at", "last_used_at"]
    list_filter = ["is_active", "client"]
    search_fields = ["name", "token_prefix", "client__name"]
    readonly_fields = ["id", "token_hash", "token_prefix", "revoked_at", "revoked_by",
                       "last_used_at", "last_used_ip", "created_at", "updated_at"]

    fieldsets = [
        ("Alapadatok", {"fields": ["client", "name", "description", "expires_at"]}),
        ("Jogosultságok", {"fields": ["scopes", "ip_whitelist"]}),
        ("Rate limiting", {"fields": ["rate_limit_per_minute", "rate_limit_per_day", "volume_limit_per_day"]}),
        ("Státusz", {"fields": ["is_active", "revoked_at", "revoked_by", "revoke_reason",
                                "last_used_at", "last_used_ip"], "classes": ["collapse"]}),
        ("Technikai", {"fields": ["id", "token_prefix", "token_hash", "created_at", "updated_at"],
                       "classes": ["collapse"]}),
    ]

    actions = ["revoke_tokens"]

    def status_badge(self, obj):
        if obj.revoked_at:
            return format_html('<span style="color:red;">● Revoked</span>')
        if not obj.is_active:
            return format_html('<span style="color:orange;">● Inactive</span>')
        if obj.expires_at and obj.expires_at < timezone.now():
            return format_html('<span style="color:gray;">● Expired</span>')
        return format_html('<span style="color:green;">● Active</span>')
    status_badge.short_description = "Status"

    def save_model(self, request, obj, form, change):
        if not change:
            instance, raw_token = ApiToken.generate(
                client=obj.client, name=obj.name,
                description=obj.description, expires_at=obj.expires_at,
                scopes=obj.scopes, ip_whitelist=obj.ip_whitelist,
                rate_limit_per_minute=obj.rate_limit_per_minute,
                rate_limit_per_day=obj.rate_limit_per_day,
                volume_limit_per_day=obj.volume_limit_per_day,
                created_by=request.user.email,
            )
            instance.save()
            messages.warning(request, format_html(
                '<strong>⚠ Token generated – copy it now, it will never be shown again:</strong><br>'
                '<code style="font-size:1.1em;background:#f0f0f0;padding:8px;display:block;margin-top:8px;">{}</code>',
                raw_token,
            ))
            return
        super().save_model(request, obj, form, change)

    @admin.action(description="Revoke selected tokens")
    def revoke_tokens(self, request, queryset):
        count = 0
        for token in queryset.filter(revoked_at__isnull=True):
            token.revoke(revoked_by=request.user.email, reason="Bulk revoke via admin")
            count += 1
        self.message_user(request, f"{count} token(s) revoked.")

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ["client"]
        return self.readonly_fields
