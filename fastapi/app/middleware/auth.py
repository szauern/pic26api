import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone

from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.db_models import ApiToken

security = HTTPBearer()


@dataclass
class TokenContext:
    token_id: str
    client_id: str
    scopes: list[str]
    rate_limit_per_minute: int | None
    rate_limit_per_day: int | None
    volume_limit_per_day: int | None


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _cache_key(token_hash: str) -> str:
    return f"auth:token:{token_hash}"


async def _get_from_cache(redis, token_hash: str) -> TokenContext | None:
    if redis is None:
        return None
    raw = await redis.get(_cache_key(token_hash))
    if not raw:
        return None
    d = json.loads(raw)
    return TokenContext(**d)


async def _set_cache(redis, token_hash: str, ctx: TokenContext) -> None:
    if redis is None:
        return
    await redis.setex(
        _cache_key(token_hash),
        settings.token_cache_ttl,
        json.dumps({
            "token_id": ctx.token_id, "client_id": ctx.client_id,
            "scopes": ctx.scopes,
            "rate_limit_per_minute": ctx.rate_limit_per_minute,
            "rate_limit_per_day": ctx.rate_limit_per_day,
            "volume_limit_per_day": ctx.volume_limit_per_day,
        }),
    )


async def _log_failure(db: AsyncSession, reason: str, client_ip: str,
                       token_prefix: str | None = None, path: str | None = None,
                       method: str | None = None, user_agent: str | None = None):
    # client_ip inet típus miatt explicit CAST szükséges
    await db.execute(
        text("""
            INSERT INTO metrics_authfailure
                (timestamp, token_prefix, failure_reason, client_ip,
                 user_agent, request_path, request_method)
            VALUES
                (:ts, :prefix, :reason, CAST(:ip AS inet),
                 :ua, :path, :method)
        """),
        {
            "ts": datetime.now(timezone.utc),
            "prefix": token_prefix,
            "reason": reason,
            "ip": client_ip,
            "ua": user_agent or "",
            "path": path or "",
            "method": method or "",
        }
    )
    await db.commit()


async def _check_rate_limit(redis, token_hash: str, ctx: TokenContext):
    if redis is None:
        return
    if ctx.rate_limit_per_minute:
        key = f"ratelimit:min:{token_hash}"
        count = await redis.incr(key)
        if count == 1:
            await redis.expire(key, settings.rate_limit_window_seconds)
        if count > ctx.rate_limit_per_minute:
            raise HTTPException(status_code=429, detail="Rate limit exceeded (per minute)",
                                headers={"Retry-After": str(settings.rate_limit_window_seconds)})

    if ctx.rate_limit_per_day:
        key = f"ratelimit:day:{token_hash}"
        count = await redis.incr(key)
        if count == 1:
            await redis.expire(key, 86400)
        if count > ctx.rate_limit_per_day:
            raise HTTPException(status_code=429, detail="Rate limit exceeded (daily quota)",
                                headers={"Retry-After": "86400"})


async def require_bearer(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> TokenContext:
    from app.redis_client import get_redis
    from app.database import AsyncSessionLocal

    token = credentials.credentials
    token_hash = _hash_token(token)
    prefix = token[:8] if len(token) >= 8 else token
    client_ip = request.client.host if request.client else "unknown"

    redis = get_redis()

    async with AsyncSessionLocal() as db:
        ctx = await _get_from_cache(redis, token_hash)

        if ctx is None:
            result = await db.execute(
                select(ApiToken).where(
                    ApiToken.token_hash == token_hash,
                    ApiToken.is_active.is_(True),
                )
            )
            record = result.scalar_one_or_none()

            if record is None:
                await _log_failure(db, "not_found", client_ip, prefix,
                                   request.url.path, request.method,
                                   request.headers.get("user-agent"))
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

            if record.revoked_at is not None:
                await _log_failure(db, "revoked", client_ip, prefix,
                                   request.url.path, request.method)
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

            if record.expires_at and record.expires_at < datetime.now(timezone.utc):
                await _log_failure(db, "expired", client_ip, prefix,
                                   request.url.path, request.method)
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

            ctx = TokenContext(
                token_id=str(record.id), client_id=str(record.client_id),
                scopes=record.scopes or [],
                rate_limit_per_minute=record.rate_limit_per_minute,
                rate_limit_per_day=record.rate_limit_per_day,
                volume_limit_per_day=record.volume_limit_per_day,
            )
            await _set_cache(redis, token_hash, ctx)

            # last_used_ip inet típus miatt explicit CAST szükséges
            await db.execute(
                text("""
                    UPDATE tokens_apitoken
                    SET last_used_at = :ts,
                        last_used_ip = CAST(:ip AS inet)
                    WHERE id = :id
                """),
                {"ts": datetime.now(timezone.utc), "ip": client_ip, "id": record.id}
            )
            await db.commit()

        await _check_rate_limit(redis, token_hash, ctx)

    return ctx


def require_scope(scope: str):
    async def _check(
        request: Request,
        credentials: HTTPAuthorizationCredentials = Depends(security),
    ) -> TokenContext:
        ctx = await require_bearer(request, credentials)
        if scope not in ctx.scopes:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail=f"Insufficient scope. Required: {scope}")
        return ctx
    return _check
