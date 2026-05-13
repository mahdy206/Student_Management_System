from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
from App.Database import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    entity = Column(String(50), nullable=False)   # e.g. "student"
    entity_id = Column(Integer, nullable=False)
    action = Column(String(20), nullable=False)    # "create", "update", "delete"
    performed_by = Column(String(255), nullable=False)
    details = Column(Text, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())