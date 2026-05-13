from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from App.Database import get_db
from App.Schemas.Student import (
    StudentCreate,
    StudentUpdate,
    StudentSelfUpdate,
    StudentResponse,
    StudentListResponse,
)
from App.Services import Student_service
from App.Auth.Jwt import get_current_user, require_admin
from App.Models.User import User

router = APIRouter(prefix="/students", tags=["Students"])


@router.get("/me", response_model=StudentResponse)
def get_my_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get the currently logged-in **student's** own profile.

    - Requires a valid Bearer token with **student** role.
    - Admins should use `GET /students/{id}` instead.
    """
    if current_user.role != "student":
        raise HTTPException(
            status_code=403, detail="Only students can access this endpoint"
        )
    return Student_service.get_student_by_user_id(db, current_user.id)


@router.put("/me", response_model=StudentResponse)
def update_my_profile(
    update_data: StudentSelfUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Student updates their **own** profile.

    Allowed fields: `phone`, `email`, `password`.
    Fields like `full_name`, `department`, `gpa` are restricted to admins.
    """
    if current_user.role != "student":
        raise HTTPException(
            status_code=403, detail="Only students can access this endpoint"
        )
    student = Student_service.get_student_by_user_id(db, current_user.id)
    admin_update = StudentUpdate(**update_data.model_dump(exclude_unset=True))
    return Student_service.update_student(
        db, student["id"], admin_update, current_user.email
    )


@router.get("/", response_model=StudentListResponse)
def get_all(
    department: Optional[str] = Query(None, description="Filter by department name"),
    min_gpa: Optional[float] = Query(None, ge=0.0, le=4.0, description="Minimum GPA filter"),
    page: int = Query(1, ge=1, description="Page number (starts at 1)"),
    size: int = Query(10, ge=1, le=100, description="Number of results per page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve students with optional filters and pagination.

    - **Admin**: returns all students with full filtering & pagination support.
    - **Student**: returns only their own profile wrapped in list format.

    Filters (`department`, `min_gpa`) only apply when called by an admin.
    """
    if current_user.role == "student":
        student = Student_service.get_student_by_user_id(db, current_user.id)
        return {"total": 1, "page": 1, "size": 1, "students": [student]}

    return Student_service.get_all_students(db, department, min_gpa, page, size)


@router.get("/{student_id}", response_model=StudentResponse)
def get_one(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get a single student record by ID.

    - **Admin**: can retrieve any student.
    - **Student**: can only retrieve their own record (returns 403 otherwise).
    """
    student = Student_service.get_student_by_id(db, student_id)

    if current_user.role == "student" and student["user_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    return student


@router.post("/", response_model=StudentResponse, status_code=201)
def create(
    student_data: StudentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    Create a new student record. **Admin only.**

    Automatically creates a linked user account with the provided credentials.
    The student can then log in using their `email` and `password`.
    """
    return Student_service.create_student(db, student_data)


@router.put("/{student_id}", response_model=StudentResponse)
def update(
    student_id: int,
    update_data: StudentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update a student record.

    - **Admin**: can update any field (`full_name`, `email`, `password`, `department`, `gpa`, `phone`).
    - **Student**: can only update their **own** record, and only the fields `phone`, `email`, `password`.
    """
    if current_user.role == "student":
        student = Student_service.get_student_by_id(db, student_id)
        if student["user_id"] != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        allowed = update_data.model_dump(exclude_unset=True)
        forbidden = {k for k in allowed if k not in ("phone", "email", "password")}
        if forbidden:
            raise HTTPException(
                status_code=403,
                detail=f"Students cannot update: {', '.join(sorted(forbidden))}",
            )

    return Student_service.update_student(
        db, student_id, update_data, current_user.email
    )


@router.delete("/{student_id}")
def delete(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    Delete a student and their linked user account. **Admin only.**

    Also removes all associated courses and audit logs cascade is handled at DB level.
    """
    return Student_service.delete_student(
        db, student_id, performed_by=current_user.email
    )