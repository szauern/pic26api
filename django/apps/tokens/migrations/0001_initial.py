import uuid
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Client",
            fields=[
                ("id", models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)),
                ("name", models.CharField(max_length=255)),
                ("email", models.EmailField(unique=True)),
                ("description", models.TextField(blank=True)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("created_by", models.CharField(blank=True, max_length=255)),
            ],
            options={"ordering": ["-created_at"], "verbose_name": "Client", "verbose_name_plural": "Clients"},
        ),
        migrations.CreateModel(
            name="ApiToken",
            fields=[
                ("id", models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)),
                ("client", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                             related_name="tokens", to="tokens.client")),
                ("token_hash", models.CharField(max_length=64, unique=True, editable=False)),
                ("token_prefix", models.CharField(max_length=8, editable=False)),
                ("name", models.CharField(max_length=255)),
                ("description", models.TextField(blank=True)),
                ("expires_at", models.DateTimeField(blank=True, null=True)),
                ("is_active", models.BooleanField(default=True)),
                ("revoked_at", models.DateTimeField(blank=True, editable=False, null=True)),
                ("revoked_by", models.CharField(blank=True, editable=False, max_length=255)),
                ("revoke_reason", models.TextField(blank=True)),
                ("scopes", models.JSONField(default=list)),
                ("ip_whitelist", models.JSONField(blank=True, default=list)),
                ("rate_limit_per_minute", models.IntegerField(blank=True, null=True)),
                ("rate_limit_per_day", models.IntegerField(blank=True, null=True)),
                ("volume_limit_per_day", models.BigIntegerField(blank=True, null=True)),
                ("last_used_at", models.DateTimeField(blank=True, editable=False, null=True)),
                ("last_used_ip", models.GenericIPAddressField(blank=True, editable=False, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("created_by", models.CharField(blank=True, max_length=255)),
            ],
            options={"ordering": ["-created_at"], "verbose_name": "API Token", "verbose_name_plural": "API Tokens"},
        ),
        migrations.RunSQL(
            sql="""
                CREATE INDEX IF NOT EXISTS idx_apitoken_active_hash
                    ON tokens_apitoken (token_hash)
                    WHERE is_active = TRUE AND revoked_at IS NULL;
                CREATE INDEX IF NOT EXISTS idx_apitoken_client
                    ON tokens_apitoken (client_id);
            """,
            reverse_sql="""
                DROP INDEX IF EXISTS idx_apitoken_active_hash;
                DROP INDEX IF EXISTS idx_apitoken_client;
            """,
        ),
    ]
