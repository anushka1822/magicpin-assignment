import time
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from core.database import get_db
from models.db import StoredContext
from models.schemas import (
    ContextPushRequest, ContextPushResponse,
    TickRequest, TickResponse,
    ReplyRequest, ReplyResponse
)
from core.composer import compose_tick_action, compose_reply_action

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

@router.post("/v1/tick", response_model=TickResponse)
async def process_tick(request: TickRequest, db: AsyncSession = Depends(get_db)):
    actions = []
    for trigger_id in request.available_triggers:
        stmt = select(StoredContext).where(
            StoredContext.scope == "trigger",
            StoredContext.context_id == trigger_id
        )
        result = await db.execute(stmt)
        trigger = result.scalar_one_or_none()
        
        if not trigger:
            continue
            
        merchant_id = trigger.payload.get("merchant_id")
        customer_id = trigger.payload.get("customer_id")
        
        # Fetch merchant
        merchant = None
        if merchant_id:
            m_stmt = select(StoredContext).where(
                StoredContext.scope == "merchant",
                StoredContext.context_id == merchant_id
            )
            m_result = await db.execute(m_stmt)
            merchant_record = m_result.scalar_one_or_none()
            if merchant_record:
                merchant = merchant_record.payload
                
        if not merchant:
            continue
            
        # Fetch category
        category = None
        category_slug = merchant.get("category_slug")
        if category_slug:
            c_stmt = select(StoredContext).where(
                StoredContext.scope == "category",
                StoredContext.context_id == category_slug
            )
            c_result = await db.execute(c_stmt)
            category_record = c_result.scalar_one_or_none()
            if category_record:
                category = category_record.payload
                
        if not category:
            continue
            
        # Fetch customer
        customer = None
        if customer_id:
            cu_stmt = select(StoredContext).where(
                StoredContext.scope == "customer",
                StoredContext.context_id == customer_id
            )
            cu_result = await db.execute(cu_stmt)
            customer_record = cu_result.scalar_one_or_none()
            if customer_record:
                customer = customer_record.payload
                
        action = await compose_tick_action(
            trigger_id=trigger_id,
            trigger_payload=trigger.payload,
            merchant=merchant,
            category=category,
            customer=customer
        )
        actions.append(action)
        
    return TickResponse(actions=actions)

@router.post("/v1/reply", response_model=ReplyResponse)
async def process_reply(request: ReplyRequest, db: AsyncSession = Depends(get_db)):
    merchant = None
    if request.merchant_id:
        m_stmt = select(StoredContext).where(
            StoredContext.scope == "merchant",
            StoredContext.context_id == request.merchant_id
        )
        m_result = await db.execute(m_stmt)
        m_record = m_result.scalar_one_or_none()
        if m_record:
            merchant = m_record.payload
            
    category = None
    if merchant and merchant.get("category_slug"):
        c_stmt = select(StoredContext).where(
            StoredContext.scope == "category",
            StoredContext.context_id == merchant.get("category_slug")
        )
        c_result = await db.execute(c_stmt)
        c_record = c_result.scalar_one_or_none()
        if c_record:
            category = c_record.payload
            
    customer = None
    if request.customer_id:
        cu_stmt = select(StoredContext).where(
            StoredContext.scope == "customer",
            StoredContext.context_id == request.customer_id
        )
        cu_result = await db.execute(cu_stmt)
        cu_record = cu_result.scalar_one_or_none()
        if cu_record:
            customer = cu_record.payload
            
    reply_req_dict = request.model_dump()
    result = await compose_reply_action(
        reply_req=reply_req_dict,
        merchant=merchant or {},
        category=category or {},
        customer=customer
    )
    
    return ReplyResponse(**result)
