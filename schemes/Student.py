import re
from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
from typing import Optional, List
from datetime import datetime

class StudentCreate(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6, description="Initial login password for the student account")
    department: str = Field(..., min_length=2, max_length=100)
    gpa: float = Field(default=0.0, ge=0.0, le=4.0)
    phone: Optional[str] = None
    # user_id is intentionally absent — assigned automatically when student is created

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v):
        if v is not None and not re.match(r"^01\d{9}$", v):
            raise ValueError("Phone must start with 01 and be 11 digits")
        return v


class StudentSelfUpdate(BaseModel):
    """Student updating own profile — phone, email, password only."""
    model_config = ConfigDict(extra='forbid')
    email:    Optional[EmailStr] = None
    password: Optional[str]     = Field(None, min_length=6)
    phone:    Optional[str]     = None

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v):
        if v is not None and not re.match(r"^01\d{9}$", v):
            raise ValueError("Phone must start with 01 and be 11 digits")
        return v


class StudentUpdate(BaseModel):
    """Admin update — can change any field."""
    full_name:  Optional[str]      = Field(None, min_length=2, max_length=100)
    email:      Optional[EmailStr] = None
    password:   Optional[str]      = Field(None, min_length=6)
    department: Optional[str]      = Field(None, min_length=2, max_length=100)
    gpa:        Optional[float]    = Field(None, ge=0.0, le=4.0)
    phone:      Optional[str]      = None

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v):
        if v is not None and not re.match(r"^01\d{9}$", v):
            raise ValueError("Phone must start with 01 and be 11 digits")
        return v


class StudentResponse(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    department: str
    gpa: float
    phone: Optional[str]
    user_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class StudentListResponse(BaseModel):
    total: int
    page: int
    size: int
    students: List[StudentResponse]
