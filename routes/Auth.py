from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Optional
from App.Database import get_db
from App.Schemas.User import UserCreate, UserResponse, LoginRequest, Token
from App.Models.User import User, RoleEnum
from App.Models.Student import Student
from App.Models.AuditLog import AuditLog
from App.Auth.Password import hash_password, verify_password
from App.Auth.Jwt import create_access_token
from App.Utils.Logger import logger
from App.Utils.Cache import delete_pattern

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=201)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new student account.

    - **email**: valid email address (must be unique)
    - **password**: minimum 6 characters
    - **role**: fixed to 'student' — admin accounts cannot be self-registered
    """
    if user_data.role == RoleEnum.admin:
        logger.warning(f"Blocked attempt to self-register as admin: {user_data.email}")
        raise HTTPException(
            status_code=403,
            detail="Admin accounts cannot be created via self-registration.",
        )

    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=user_data.email,
        hashed_password=hash_password(user_data.password),
        role=RoleEnum.student,
    )
    db.add(user)
    db.flush()

    placeholder = Student(
        user_id=user.id,
        full_name="(Pending)",
        email=user_data.email,
        department="(Pending)",
        gpa=0.0,
        phone=None,
    )
    db.add(placeholder)
    db.flush()

    db.add(
        AuditLog(
            entity="student",
            entity_id=placeholder.id,
            action="create",
            performed_by=user_data.email,
            details="Self-registered via /auth/register",
        )
    )
    db.commit()
    db.refresh(user)

    delete_pattern("students:all:*")
    logger.info(f"New student registered: {user.email}")
    return user


@router.post("/login", response_model=Token)
async def login(
    request: Request,
    db: Session = Depends(get_db),
    # Explicit form-data parameters — visible in Swagger UI and OpenAPI schema
    username: Optional[str] = Form(default=None, description="Email address (form-data / Swagger Authorize)"),
    password: Optional[str] = Form(default=None, description="Password (form-data / Swagger Authorize)"),
):
    """
    Login and receive a JWT access token.

    Accepts **both** formats:
    - **JSON body**: `{"email": "...", "password": "..."}`
    - **Form data**: `username=...&password=...` (used by Swagger UI Authorize button)

    Returns a bearer token to be included in subsequent requests as:
    `Authorization: Bearer <token>`
    """
    content_type = request.headers.get("content-type", "")

    if "application/json" in content_type:
        body = await request.json()
        email = body.get("email") or body.get("username")
        pwd = body.get("password")
    else:
        # form-data — prefer the explicit Form params; fall back to raw form email field
        form = await request.form()
        email = username or form.get("email")
        pwd = password or form.get("password")

    if not email or not pwd:
        raise HTTPException(status_code=422, detail="email and password are required")

    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(pwd, user.hashed_password):
        logger.warning(f"Failed login attempt for: {email}")
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token({"sub": user.email, "role": user.role})
    logger.info(f"User logged in: {user.email} (role={user.role})")
    return {"access_token": token, "token_type": "bearer"}
