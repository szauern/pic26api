import hashlib
import uuid
from django.db import models


class Language(models.Model):
    code = models.CharField(max_length=5, primary_key=True)
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["code"]
        verbose_name = "Language"
        verbose_name_plural = "Languages"

    def __str__(self):
        return f"{self.name} ({self.code})"

    def save(self, *args, **kwargs):
        if self.is_default:
            Language.objects.exclude(pk=self.pk).filter(is_default=True).update(is_default=False)
        super().save(*args, **kwargs)


class Namespace(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["code"]
        verbose_name = "Namespace"
        verbose_name_plural = "Namespaces"

    def __str__(self):
        return self.code


class TranslationKey(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    namespace = models.ForeignKey(Namespace, on_delete=models.CASCADE, related_name="keys")
    key = models.CharField(max_length=500)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["namespace", "key"]
        unique_together = [["namespace", "key"]]
        verbose_name = "Translation Key"
        verbose_name_plural = "Translation Keys"

    def __str__(self):
        return f"{self.namespace.code}.{self.key}"


class Translation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    translation_key = models.ForeignKey(TranslationKey, on_delete=models.CASCADE, related_name="translations")
    language = models.ForeignKey(Language, on_delete=models.CASCADE, related_name="translations")
    value = models.TextField()
    external_id = models.CharField(max_length=255, blank=True)
    external_source = models.CharField(max_length=100, blank=True)
    synced_at = models.DateTimeField(null=True, blank=True)
    checksum = models.CharField(max_length=64, blank=True, editable=False)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["translation_key", "language"]
        unique_together = [["translation_key", "language"]]
        verbose_name = "Translation"
        verbose_name_plural = "Translations"

    def __str__(self):
        return f"{self.translation_key} [{self.language_id}]"

    def save(self, *args, **kwargs):
        self.checksum = hashlib.sha256(self.value.encode()).hexdigest()
        super().save(*args, **kwargs)
        self._invalidate_cache()

    def _invalidate_cache(self):
        try:
            from django.core.cache import cache
            ns = self.translation_key.namespace.code
            lang = self.language_id
            key = self.translation_key.key
            cache.delete(f"trans:{lang}:{ns}:{key}")
            cache.delete(f"trans:{lang}:{ns}")
        except Exception:
            pass
