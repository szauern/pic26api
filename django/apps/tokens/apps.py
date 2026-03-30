from django.apps import AppConfig

class TokensConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.tokens"
    verbose_name = "API Token Management"

    def ready(self):
        import apps.tokens.signals  # noqa
