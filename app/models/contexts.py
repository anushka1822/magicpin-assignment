from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel

class CategoryContext(BaseModel):
    slug: str
    offer_catalog: List[Dict[str, Any]]
    voice: Dict[str, Any]
    peer_stats: Dict[str, Any]
    digest: List[Dict[str, Any]]
    patient_content_library: List[Dict[str, Any]]
    seasonal_beats: List[Dict[str, Any]]
    trend_signals: List[Dict[str, Any]]

class MerchantContext(BaseModel):
    merchant_id: str
    category_slug: str
    identity: Dict[str, Any]
    subscription: Dict[str, Any]
    performance: Dict[str, Any]
    offers: List[Dict[str, Any]]
    conversation_history: List[Dict[str, Any]]
    customer_aggregate: Dict[str, Any]
    signals: List[str]

class TriggerContext(BaseModel):
    id: str
    scope: Literal["merchant", "customer"]
    kind: str
    source: Literal["external", "internal"]
    merchant_id: str
    customer_id: Optional[str] = None
    payload: Dict[str, Any]
    urgency: int
    suppression_key: str
    expires_at: datetime

class CustomerContext(BaseModel):
    customer_id: str
    merchant_id: str
    identity: Dict[str, Any]
    relationship: Dict[str, Any]
    state: Literal["new", "active", "lapsed_soft", "lapsed_hard", "churned"]
    preferences: Dict[str, Any]
    consent: Dict[str, Any]
