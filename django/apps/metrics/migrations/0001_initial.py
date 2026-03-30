import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = [("tokens", "0001_initial")]

    operations = [
        migrations.CreateModel(
            name="TokenUsageDaily",
            fields=[
                ("id", models.BigAutoField(primary_key=True)),
                ("token", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                            related_name="daily_usage", to="tokens.apitoken")),
                ("date", models.DateField()),
                ("request_count", models.IntegerField(default=0)),
                ("success_count", models.IntegerField(default=0)),
                ("error_count", models.IntegerField(default=0)),
                ("bytes_sent", models.BigIntegerField(default=0)),
                ("bytes_received", models.BigIntegerField(default=0)),
            ],
            options={"ordering": ["-date"], "unique_together": {("token", "date")}},
        ),
        migrations.CreateModel(
            name="AuthFailure",
            fields=[
                ("id", models.BigAutoField(primary_key=True)),
                ("timestamp", models.DateTimeField()),
                ("token_prefix", models.CharField(blank=True, max_length=8, null=True)),
                ("failure_reason", models.CharField(max_length=50)),
                ("client_ip", models.GenericIPAddressField()),
                ("user_agent", models.TextField(blank=True)),
                ("request_path", models.CharField(blank=True, max_length=500)),
                ("request_method", models.CharField(blank=True, max_length=10)),
            ],
            options={"ordering": ["-timestamp"]},
        ),
        migrations.CreateModel(
            name="SyncLog",
            fields=[
                ("id", models.BigAutoField(primary_key=True)),
                ("started_at", models.DateTimeField()),
                ("finished_at", models.DateTimeField(blank=True, null=True)),
                ("source", models.CharField(max_length=100)),
                ("status", models.CharField(default="running", max_length=20)),
                ("keys_added", models.IntegerField(default=0)),
                ("keys_updated", models.IntegerField(default=0)),
                ("keys_removed", models.IntegerField(default=0)),
                ("errors_count", models.IntegerField(default=0)),
                ("error_details", models.JSONField(blank=True, null=True)),
                ("triggered_by", models.CharField(blank=True, max_length=100)),
            ],
            options={"ordering": ["-started_at"]},
        ),
        migrations.RunSQL(
            sql="""
                CREATE INDEX IF NOT EXISTS idx_tokenusage_token_date
                    ON metrics_tokenusagedaily (token_id, date DESC);
                CREATE INDEX IF NOT EXISTS idx_authfailure_timestamp
                    ON metrics_authfailure (timestamp DESC);
                CREATE INDEX IF NOT EXISTS idx_authfailure_ip
                    ON metrics_authfailure (client_ip, timestamp DESC);
                CREATE INDEX IF NOT EXISTS idx_synclog_started
                    ON metrics_synclog (started_at DESC);
            """,
            reverse_sql="""
                DROP INDEX IF EXISTS idx_tokenusage_token_date;
                DROP INDEX IF EXISTS idx_authfailure_timestamp;
                DROP INDEX IF EXISTS idx_authfailure_ip;
                DROP INDEX IF EXISTS idx_synclog_started;
            """,
        ),
    ]
