from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.sql import func
from App.Database import Base

class Student(Base):
    __tablename__ = "students"

    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey("users.id"), unique=True)
    full_name  = Column(String(100), nullable=False)
    email      = Column(String(255), unique=True, nullable=False)
    department = Column(String(100), nullable=False, index=True)
    gpa        = Column(Float, default=0.0, index=True)
    phone      = Column(String(20), nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
