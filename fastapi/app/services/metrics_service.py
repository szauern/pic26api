from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert
from app.models.db_models import TokenUsageDaily


async def record_request(db: AsyncSession, token_id: str, success: bool,
                         bytes_sent: int = 0, bytes_received: int = 0):
    stmt = insert(TokenUsageDaily).values(
        token_id=token_id, date=date.today(),
        request_count=1,
        success_count=1 if success else 0,
        error_count=0 if success else 1,
        bytes_sent=bytes_sent, bytes_received=bytes_received,
    ).on_conflict_do_update(
        constraint="metrics_tokenusagedaily_token_id_date_key",
        set_={
            "request_count": TokenUsageDaily.request_count + 1,
            "success_count": TokenUsageDaily.success_count + (1 if success else 0),
            "error_count": TokenUsageDaily.error_count + (0 if success else 1),
            "bytes_sent": TokenUsageDaily.bytes_sent + bytes_sent,
            "bytes_received": TokenUsageDaily.bytes_received + bytes_received,
        }
    )
    await db.execute(stmt)
    await db.commit()
