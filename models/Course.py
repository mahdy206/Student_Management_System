from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.sql import func
from App.Database import Base

class Course(Base):
    __tablename__ = "courses"

    id           = Column(Integer, primary_key=True, index=True)
    student_id   = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    course_name  = Column(String(150), nullable=False)
    course_code  = Column(String(20),  nullable=False)
    credit_hours = Column(Integer,     nullable=False, default=3)
    grade        = Column(Float,       nullable=True)
    semester     = Column(String(50),  nullable=False)
    created_at   = Column(DateTime(timezone=True), server_default=func.now())
    updated_at   = Column(DateTime(timezone=True), onupdate=func.now())
