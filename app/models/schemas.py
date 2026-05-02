from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel

class ContextPushRequest(BaseModel):
    scope: str
    context_id: str
    version: int
    payload: Dict[str, Any]
    delivered_at: datetime

class ContextPushResponse(BaseModel):
    accepted: bool
    ack_id: Optional[str] = None
    stored_at: Optional[datetime] = None
    reason: Optional[str] = None
    current_version: Optional[int] = None

class TickRequest(BaseModel):
    now: datetime
    available_triggers: List[str] = []

class TickResponse(BaseModel):
    actions: List[Dict[str, Any]]

class ReplyRequest(BaseModel):
    conversation_id: str
    merchant_id: Optional[str] = None
    customer_id: Optional[str] = None
    from_role: str
    message: str
    received_at: datetime
    turn_number: int

class ReplyResponse(BaseModel):
    action: Literal["send", "wait", "end"]
    body: Optional[str] = None
    cta: Optional[str] = None
    wait_seconds: Optional[int] = None
    rationale: str
