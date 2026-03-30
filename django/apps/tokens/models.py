import hashlib
import secrets
import uuid
from django.db import models


class Client(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Client"
        verbose_name_plural = "Clients"

    def __str__(self):
        return f"{self.name} <{self.email}>"


class ApiToken(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="tokens")
    token_hash = models.CharField(max_length=64, unique=True, editable=False)
    token_prefix = models.CharField(max_length=8, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    revoked_at = models.DateTimeField(null=True, blank=True, editable=False)
    revoked_by = models.CharField(max_length=255, blank=True, editable=False)
    revoke_reason = models.TextField(blank=True)
    scopes = models.JSONField(default=list)
    ip_whitelist = models.JSONField(default=list, blank=True)
    rate_limit_per_minute = models.IntegerField(null=True, blank=True)
    rate_limit_per_day = models.IntegerField(null=True, blank=True)
    volume_limit_per_day = models.BigIntegerField(null=True, blank=True)
    last_used_at = models.DateTimeField(null=True, blank=True, editable=False)
    last_used_ip = models.GenericIPAddressField(null=True, blank=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "API Token"
        verbose_name_plural = "API Tokens"

    def __str__(self):
        return f"{self.name} ({self.token_prefix}...)"

    @classmethod
    def generate(cls, client, name, **kwargs):
        raw_token = secrets.token_hex(32)
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        instance = cls(
            client=client, name=name,
            token_hash=token_hash,
            token_prefix=raw_token[:8],
            **kwargs,
        )
        return instance, raw_token

    def revoke(self, revoked_by="", reason=""):
        from django.utils import timezone
        self.revoked_at = timezone.now()
        self.revoked_by = revoked_by
        self.revoke_reason = reason
        self.is_active = False
        self.save(update_fields=["revoked_at", "revoked_by", "revoke_reason", "is_active", "updated_at"])
        try:
            from django.core.cache import cache
            cache.delete(f"auth:token:{self.token_hash}")
        except Exception:
            pass
