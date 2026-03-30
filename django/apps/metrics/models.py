from django.db import models
from apps.tokens.models import ApiToken


class TokenUsageDaily(models.Model):
    token = models.ForeignKey(ApiToken, on_delete=models.CASCADE, related_name="daily_usage")
    date = models.DateField()
    request_count = models.IntegerField(default=0)
    success_count = models.IntegerField(default=0)
    error_count = models.IntegerField(default=0)
    bytes_sent = models.BigIntegerField(default=0)
    bytes_received = models.BigIntegerField(default=0)

    class Meta:
        unique_together = [["token", "date"]]
        ordering = ["-date"]
        verbose_name = "Token Usage (Daily)"
        verbose_name_plural = "Token Usage (Daily)"

    def __str__(self):
        return f"{self.token.name} – {self.date} ({self.request_count} reqs)"


class AuthFailure(models.Model):
    REASONS = [
        ("not_found", "Token not found"),
        ("revoked", "Token revoked"),
        ("expired", "Token expired"),
        ("ip_not_whitelisted", "IP not whitelisted"),
        ("scope_insufficient", "Insufficient scope"),
        ("rate_limit_exceeded", "Rate limit exceeded"),
    ]
    timestamp = models.DateTimeField()
    token_prefix = models.CharField(max_length=8, blank=True, null=True)
    failure_reason = models.CharField(max_length=50, choices=REASONS)
    client_ip = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    request_path = models.CharField(max_length=500, blank=True)
    request_method = models.CharField(max_length=10, blank=True)

    class Meta:
        ordering = ["-timestamp"]
        verbose_name = "Auth Failure"
        verbose_name_plural = "Auth Failures"

    def __str__(self):
        return f"{self.failure_reason} from {self.client_ip}"


class SyncLog(models.Model):
    STATUS = [
        ("running", "Running"), ("success", "Success"),
        ("partial", "Partial"), ("failed", "Failed"),
    ]
    started_at = models.DateTimeField()
    finished_at = models.DateTimeField(null=True, blank=True)
    source = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=STATUS, default="running")
    keys_added = models.IntegerField(default=0)
    keys_updated = models.IntegerField(default=0)
    keys_removed = models.IntegerField(default=0)
    errors_count = models.IntegerField(default=0)
    error_details = models.JSONField(null=True, blank=True)
    triggered_by = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ["-started_at"]
        verbose_name = "Sync Log"
        verbose_name_plural = "Sync Logs"

    def __str__(self):
        return f"{self.source} – {self.status} @ {self.started_at:%Y-%m-%d %H:%M}"
