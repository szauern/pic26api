from django.contrib import admin
from django.utils.html import format_html
from .models import Language, Namespace, TranslationKey, Translation


@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "is_active", "is_default"]
    list_editable = ["is_active", "is_default"]


@admin.register(Namespace)
class NamespaceAdmin(admin.ModelAdmin):
    list_display = ["code", "description", "is_active"]
    search_fields = ["code"]


class TranslationInline(admin.TabularInline):
    model = Translation
    extra = 1
    fields = ["language", "value", "is_verified"]


@admin.register(TranslationKey)
class TranslationKeyAdmin(admin.ModelAdmin):
    list_display = ["key", "namespace", "is_active"]
    list_filter = ["namespace", "is_active"]
    search_fields = ["key"]
    inlines = [TranslationInline]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(Translation)
class TranslationAdmin(admin.ModelAdmin):
    list_display = ["translation_key", "language", "value_preview", "is_verified", "synced_at"]
    list_filter = ["language", "is_verified"]
    search_fields = ["translation_key__key", "value"]
    readonly_fields = ["id", "checksum", "created_at", "updated_at"]
    actions = ["mark_verified", "invalidate_cache"]

    def value_preview(self, obj):
        return obj.value[:60] + "..." if len(obj.value) > 60 else obj.value
    value_preview.short_description = "Value"

    @admin.action(description="Mark selected as verified")
    def mark_verified(self, request, queryset):
        count = queryset.update(is_verified=True)
        self.message_user(request, f"{count} translation(s) marked as verified.")

    @admin.action(description="Invalidate Redis cache")
    def invalidate_cache(self, request, queryset):
        for t in queryset.select_related("translation_key__namespace"):
            t._invalidate_cache()
        self.message_user(request, "Cache invalidated.")
