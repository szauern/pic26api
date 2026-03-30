import json
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import settings
from app.models.db_models import Translation, TranslationKey, TranslationNamespace, Language


def _single_key(lang: str, ns: str, key: str) -> str:
    return f"trans:{lang}:{ns}:{key}"

def _ns_key(lang: str, ns: str) -> str:
    return f"trans:{lang}:{ns}"


async def get_translation(redis, db: AsyncSession, lang: str, ns: str, key: str,
                           fallback: str = "en") -> str | None:
    cache_key = _single_key(lang, ns, key)
    if redis is not None:
        cached = await redis.get(cache_key)
        if cached is not None:
            return cached or None

    result = await db.execute(
        select(Translation.value)
        .join(TranslationKey, Translation.key_id == TranslationKey.id)
        .join(TranslationNamespace, TranslationKey.namespace_id == TranslationNamespace.id)
        .where(TranslationNamespace.code == ns, TranslationKey.key == key,
               TranslationKey.is_active.is_(True), Translation.language_id == lang)
    )
    value = result.scalar_one_or_none()

    if value is None and lang != fallback:
        result = await db.execute(
            select(Translation.value)
            .join(TranslationKey, Translation.key_id == TranslationKey.id)
            .join(TranslationNamespace, TranslationKey.namespace_id == TranslationNamespace.id)
            .where(TranslationNamespace.code == ns, TranslationKey.key == key,
                   TranslationKey.is_active.is_(True), Translation.language_id == fallback)
        )
        value = result.scalar_one_or_none()

    if redis is not None:
        await redis.setex(cache_key, settings.translation_cache_ttl, value or "")
    return value


async def get_namespace_translations(redis, db: AsyncSession, lang: str, ns: str) -> dict:
    if redis is not None:
        cached = await redis.get(_ns_key(lang, ns))
        if cached is not None:
            return json.loads(cached)

    result = await db.execute(
        select(TranslationKey.key, Translation.value)
        .join(TranslationKey, Translation.key_id == TranslationKey.id)
        .join(TranslationNamespace, TranslationKey.namespace_id == TranslationNamespace.id)
        .where(TranslationNamespace.code == ns, TranslationKey.is_active.is_(True),
               Translation.language_id == lang)
    )
    translations = {row.key: row.value for row in result}

    if redis is not None:
        await redis.setex(_ns_key(lang, ns), settings.translation_cache_ttl, json.dumps(translations))
    return translations


async def get_active_languages(redis, db: AsyncSession) -> list[dict]:
    if redis is not None:
        cached = await redis.get("meta:languages")
        if cached:
            return json.loads(cached)

    result = await db.execute(select(Language).where(Language.is_active.is_(True)))
    langs = [{"code": l.code, "name": l.name, "is_default": l.is_default} for l in result.scalars()]

    if redis is not None:
        await redis.setex("meta:languages", settings.translation_cache_ttl, json.dumps(langs))
    return langs


async def invalidate_namespace_cache(redis, ns: str) -> int:
    if redis is None:
        return 0
    deleted = 0
    async for key in redis.scan_iter(f"trans:*:{ns}*", count=100):
        await redis.delete(key)
        deleted += 1
    return deleted
