import time
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from core.database import get_db
from models.db import StoredContext
from models.schemas import ContextPushRequest, ContextPushResponse

router = APIRouter()

START_TIME = time.time()

@router.get("/v1/healthz")
async def healthz(db: AsyncSession = Depends(get_db)):
    uptime_seconds = int(time.time() - START_TIME)
    
    stmt = select(StoredContext.scope, func.count(StoredContext.id)).group_by(StoredContext.scope)
    result = await db.execute(stmt)
    counts = dict(result.all())
    
    contexts_loaded = {
        "category": counts.get("category", 0),
        "merchant": counts.get("merchant", 0),
        "customer": counts.get("customer", 0),
        "trigger": counts.get("trigger", 0),
    }
    
    return {
        "status": "ok",
        "uptime_seconds": uptime_seconds,
        "contexts_loaded": contexts_loaded
    }

@router.get("/v1/metadata")
async def metadata():
    return {
        "team_name": "Antigravity",
        "team_members": ["AI", "Human"],
        "model": "TBD",
        "approach": "Stateful FastAPI with Postgres",
        "version": "1.0.0"
    }

@router.post("/v1/context", response_model=ContextPushResponse)
async def push_context(request: ContextPushRequest, db: AsyncSession = Depends(get_db)):
    stmt = select(StoredContext).where(
        StoredContext.scope == request.scope,
        StoredContext.context_id == request.context_id
    )
    result = await db.execute(stmt)
    record = result.scalar_one_or_none()
    
    now = datetime.utcnow()
    
    if record:
        if request.version <= record.version:
            raise HTTPException(
                status_code=409,
                detail={
                    "accepted": False,
                    "reason": "stale_version",
                    "current_version": record.version
                }
            )
        
        record.version = request.version
        record.payload = request.payload
        record.updated_at = now
    else:
        record = StoredContext(
            scope=request.scope,
            context_id=request.context_id,
            version=request.version,
            payload=request.payload,
            updated_at=now
        )
        db.add(record)
        
    await db.commit()
    
    return ContextPushResponse(
        accepted=True,
        ack_id=f"ack_{request.context_id}_v{request.version}",
        stored_at=now
    )
