from datetime import datetime
from sqlalchemy import Column, Integer, String, JSON, DateTime, UniqueConstraint
from core.database import Base

class StoredContext(Base):
    __tablename__ = "stored_contexts"

    id = Column(Integer, primary_key=True, index=True)
    scope = Column(String, index=True, nullable=False)
    context_id = Column(String, index=True, nullable=False)
    version = Column(Integer, nullable=False)
    payload = Column(JSON, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('scope', 'context_id', name='uq_scope_context_id'),
    )
