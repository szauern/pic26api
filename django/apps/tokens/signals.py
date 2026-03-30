from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.db import connection

GRANTS = [
    # Tokens - olvasás
    "GRANT SELECT ON tokens_client TO fastapi_user",
    "GRANT SELECT ON tokens_apitoken TO fastapi_user",
    # Tokens - last_used frissítés (inet cast miatt raw SQL-lel kezeljük, de jogosultság kell)
    "GRANT UPDATE (last_used_at, last_used_ip) ON tokens_apitoken TO fastapi_user",
    # Translations - olvasás
    "GRANT SELECT ON translations_language TO fastapi_user",
    "GRANT SELECT ON translations_namespace TO fastapi_user",
    "GRANT SELECT ON translations_translationkey TO fastapi_user",
    "GRANT SELECT ON translations_translation TO fastapi_user",
    # Translations - webhook import
    "GRANT INSERT, UPDATE ON translations_translationkey TO fastapi_user",
    "GRANT INSERT, UPDATE ON translations_translation TO fastapi_user",
    # Metrics - írás
    "GRANT INSERT, UPDATE ON metrics_tokenusagedaily TO fastapi_user",
    "GRANT USAGE, SELECT ON SEQUENCE metrics_tokenusagedaily_id_seq TO fastapi_user",
    "GRANT INSERT ON metrics_authfailure TO fastapi_user",
    "GRANT USAGE, SELECT ON SEQUENCE metrics_authfailure_id_seq TO fastapi_user",
    "GRANT INSERT, UPDATE ON metrics_synclog TO fastapi_user",
    "GRANT USAGE, SELECT ON SEQUENCE metrics_synclog_id_seq TO fastapi_user",
]


@receiver(post_migrate)
def grant_fastapi_permissions(sender, **kwargs):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 FROM pg_roles WHERE rolname = 'fastapi_user'")
            if cursor.fetchone():
                for grant in GRANTS:
                    try:
                        cursor.execute(grant)
                    except Exception:
                        pass
    except Exception:
        pass
