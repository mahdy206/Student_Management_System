from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime


class CourseCreate(BaseModel):
    course_name:  str   = Field(..., min_length=2, max_length=150)
    course_code:  str   = Field(..., min_length=2, max_length=20)
    credit_hours: int   = Field(default=3, ge=1, le=6)
    grade:        Optional[float] = Field(None, ge=0.0, le=100.0)
    semester:     str   = Field(..., min_length=2, max_length=50)


class CourseUpdate(BaseModel):
    course_name:  Optional[str]   = Field(None, min_length=2, max_length=150)
    course_code:  Optional[str]   = Field(None, min_length=2, max_length=20)
    credit_hours: Optional[int]   = Field(None, ge=1, le=6)
    grade:        Optional[float] = Field(None, ge=0.0, le=100.0)
    semester:     Optional[str]   = Field(None, min_length=2, max_length=50)


class CourseResponse(BaseModel):
    id:           int
    student_id:   int
    course_name:  str
    course_code:  str
    credit_hours: int
    grade:        Optional[float]
    semester:     str
    created_at:   Optional[datetime] = None
    updated_at:   Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class CourseListResponse(BaseModel):
    total:   int
    courses: List[CourseResponse]
