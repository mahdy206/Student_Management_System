from pydantic import BaseModel, EmailStr, ConfigDict
from App.Models.User import RoleEnum

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: RoleEnum = RoleEnum.student

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    role: RoleEnum

    model_config = ConfigDict(from_attributes=True)

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str