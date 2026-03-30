import uuid
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Language",
            fields=[
                ("code", models.CharField(max_length=5, primary_key=True)),
                ("name", models.CharField(max_length=100)),
                ("is_active", models.BooleanField(default=True)),
                ("is_default", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"ordering": ["code"], "verbose_name": "Language", "verbose_name_plural": "Languages"},
        ),
        migrations.CreateModel(
            name="Namespace",
            fields=[
                ("id", models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)),
                ("code", models.CharField(max_length=100, unique=True)),
                ("description", models.TextField(blank=True)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"ordering": ["code"], "verbose_name": "Namespace", "verbose_name_plural": "Namespaces"},
        ),
        migrations.CreateModel(
            name="TranslationKey",
            fields=[
                ("id", models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)),
                ("namespace", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                                related_name="keys", to="translations.namespace")),
                ("key", models.CharField(max_length=500)),
                ("description", models.TextField(blank=True)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["namespace", "key"],
                "unique_together": {("namespace", "key")},
                "verbose_name": "Translation Key",
                "verbose_name_plural": "Translation Keys",
            },
        ),
        migrations.CreateModel(
            name="Translation",
            fields=[
                ("id", models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)),
                ("translation_key", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                                      related_name="translations",
                                                      to="translations.translationkey")),
                ("language", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                               related_name="translations",
                                               to="translations.language")),
                ("value", models.TextField()),
                ("external_id", models.CharField(blank=True, max_length=255)),
                ("external_source", models.CharField(blank=True, max_length=100)),
                ("synced_at", models.DateTimeField(blank=True, null=True)),
                ("checksum", models.CharField(blank=True, editable=False, max_length=64)),
                ("is_verified", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["translation_key", "language"],
                "unique_together": {("translation_key", "language")},
                "verbose_name": "Translation",
                "verbose_name_plural": "Translations",
            },
        ),
        # FONTOS: Django ForeignKey -> language_id oszlopnév (nem language_code)
        migrations.RunSQL(
            sql="""
                CREATE INDEX IF NOT EXISTS idx_translationkey_active_ns
                    ON translations_translationkey (namespace_id)
                    WHERE is_active = TRUE;
                CREATE INDEX IF NOT EXISTS idx_translation_key_lang
                    ON translations_translation (translation_key_id, language_id);
                CREATE INDEX IF NOT EXISTS idx_translation_synced
                    ON translations_translation (synced_at DESC)
                    WHERE synced_at IS NOT NULL;
            """,
            reverse_sql="""
                DROP INDEX IF EXISTS idx_translationkey_active_ns;
                DROP INDEX IF EXISTS idx_translation_key_lang;
                DROP INDEX IF EXISTS idx_translation_synced;
            """,
        ),
    ]
