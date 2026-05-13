from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from App.Database import get_db
from App.Schemas.Course import CourseCreate, CourseUpdate, CourseResponse, CourseListResponse
from App.Services import Course_service
from App.Auth.Jwt import get_current_user, require_admin
from App.Models.User import User
from App.Services.Student_service import get_student_by_id

router = APIRouter(prefix="/students/{student_id}/courses", tags=["Courses"])


def _check_student_access(student_id: int, current_user: User, db: Session):
    """Students can only access their own courses."""
    if current_user.role == "student":
        student = get_student_by_id(db, student_id)
        if student["user_id"] != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")


@router.get("/", response_model=CourseListResponse)
def list_courses(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all courses for a student. Admin sees any student; student sees only their own."""
    _check_student_access(student_id, current_user, db)
    return Course_service.get_courses_for_student(db, student_id)


@router.get("/{course_id}", response_model=CourseResponse)
def get_course(
    student_id: int,
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a single course. Admin sees any; student sees only their own."""
    _check_student_access(student_id, current_user, db)
    return Course_service.get_course_by_id(db, student_id, course_id)


@router.post("/", response_model=CourseResponse, status_code=201)
def add_course(
    student_id: int,
    data: CourseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Admin registers a course for a student."""
    return Course_service.create_course(db, student_id, data, current_user.email)


@router.put("/{course_id}", response_model=CourseResponse)
def update_course(
    student_id: int,
    course_id: int,
    data: CourseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Admin updates a course (e.g. assigns a grade)."""
    return Course_service.update_course(db, student_id, course_id, data, current_user.email)


@router.delete("/{course_id}")
def delete_course(
    student_id: int,
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Admin removes a course from a student."""
    return Course_service.delete_course(db, student_id, course_id, current_user.email)
