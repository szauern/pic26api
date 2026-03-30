#!/bin/sh
set -e

echo "=== Waiting for database ==="
until python -c "
import asyncio, asyncpg, os
async def check():
    url = os.environ['DATABASE_URL'].replace('postgresql+asyncpg://', 'postgresql://')
    conn = await asyncpg.connect(url, timeout=3)
    await conn.close()
asyncio.run(check())
" 2>/dev/null; do
  echo "DB not ready, retrying..."
  sleep 2
done
echo "DB ready"

echo "=== Waiting for Redis ==="
until python -c "
import redis, os
redis.from_url(os.environ['REDIS_URL']).ping()
" 2>/dev/null; do
  echo "Redis not ready, retrying..."
  sleep 2
done
echo "Redis ready"

echo "=== Starting FastAPI ==="
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
