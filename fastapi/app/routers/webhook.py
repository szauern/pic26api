import hashlib
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from app.middleware.auth import require_scope, TokenContext
from app.models.db_models import Translation, TranslationKey, TranslationNamespace
from app.services.translation_service import invalidate_namespace_cache
from app.redis_client import get_redis
from app.database import AsyncSessionLocal

router = APIRouter(prefix="/api/webhook", tags=["webhook"])


class ImportPayload(BaseModel):
    language: str
    namespace: str
    translations: dict[str, str]
    source: str = "webhook"


class ImportResult(BaseModel):
    language: str
    namespace: str
    added: int
    updated: int
    errors: int
    cache_invalidated: int
    error_details: list = []


@router.post("/translations/import", response_model=ImportResult)
async def import_translations(
    payload: ImportPayload,
    request: Request,
    ctx: TokenContext = Depends(require_scope("write:translations")),
):
    added = updated = errors = 0
    error_details = []

    async with AsyncSessionLocal() as db:
        # Namespace ellenőrzés
        ns_result = await db.execute(
            select(TranslationNamespace).where(TranslationNamespace.code == payload.namespace)
        )
        namespace = ns_result.scalar_one_or_none()
        if namespace is None:
            raise HTTPException(404, detail=f"Namespace not found: {payload.namespace}")

        # Fordítások importálása
        for key_str, value in payload.translations.items():
            try:
                key_result = await db.execute(
                    select(TranslationKey).where(
                        TranslationKey.namespace_id == namespace.id,
                        TranslationKey.key == key_str,
                    )
                )
                trans_key = key_result.scalar_one_or_none()

                if trans_key is None:
                    trans_key = TranslationKey(
                        id=uuid.uuid4(), namespace_id=namespace.id,
                        key=key_str, is_active=True, description="",
                    )
                    db.add(trans_key)
                    await db.flush()
                    added += 1
                else:
                    updated += 1

                checksum = hashlib.sha256(value.encode()).hexdigest()
                stmt = pg_insert(Translation).values(
                    id=uuid.uuid4(), key_id=trans_key.id,
                    language_id=payload.language, value=value,
                    external_source=payload.source,
                    synced_at=datetime.now(timezone.utc),
                    checksum=checksum, is_verified=False,
                ).on_conflict_do_update(
                    constraint="translations_translation_translation_key_id_language_id_key",
                    set_={
                        "value": value,
                        "synced_at": datetime.now(timezone.utc),
                        "checksum": checksum,
                    },
                )
                await db.execute(stmt)

            except Exception as e:
                errors += 1
                error_details.append({"key": key_str, "error": str(e)})

        await db.commit()

    # Cache invalidálás
    cache_deleted = await invalidate_namespace_cache(get_redis(), payload.namespace)

    return ImportResult(
        language=payload.language,
        namespace=payload.namespace,
        added=added,
        updated=updated,
        errors=errors,
        cache_invalidated=cache_deleted,
        error_details=error_details,
    )
