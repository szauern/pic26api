from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from app.middleware.auth import require_bearer, TokenContext
from app.services.translation_service import (
    get_translation, get_namespace_translations, get_active_languages
)
from app.redis_client import get_redis
from app.database import AsyncSessionLocal

router = APIRouter(prefix="/api/translations", tags=["translations"])


class TranslationResponse(BaseModel):
    key: str
    language: str
    namespace: str
    value: str | None

class NamespaceResponse(BaseModel):
    language: str
    namespace: str
    translations: dict[str, str]

class LanguageItem(BaseModel):
    code: str
    name: str
    is_default: bool


@router.get("/languages", response_model=list[LanguageItem])
async def list_languages(request: Request, ctx: TokenContext = Depends(require_bearer)):
    async with AsyncSessionLocal() as db:
        langs = await get_active_languages(get_redis(), db)
    return [LanguageItem(**l) for l in langs]


@router.get("/{language}/{namespace}/{key}", response_model=TranslationResponse)
async def get_single(language: str, namespace: str, key: str,
                     request: Request, ctx: TokenContext = Depends(require_bearer)):
    async with AsyncSessionLocal() as db:
        value = await get_translation(get_redis(), db, language, namespace, key)
    if value is None:
        raise HTTPException(404, detail=f"Translation not found: {namespace}.{key} [{language}]")
    return TranslationResponse(key=key, language=language, namespace=namespace, value=value)


@router.get("/{language}/{namespace}", response_model=NamespaceResponse)
async def get_namespace(language: str, namespace: str,
                        request: Request, ctx: TokenContext = Depends(require_bearer)):
    async with AsyncSessionLocal() as db:
        translations = await get_namespace_translations(get_redis(), db, language, namespace)
    return NamespaceResponse(language=language, namespace=namespace, translations=translations)
