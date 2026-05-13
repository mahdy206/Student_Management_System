from sqlalchemy.orm import Session
from fastapi import HTTPException
from App.Models.Course import Course
from App.Models.Student import Student
from App.Models.AuditLog import AuditLog
from App.Schemas.Course import CourseCreate, CourseUpdate
from App.Utils.Cache import get_cache, set_cache, delete_cache, delete_pattern
from App.Utils.Logger import logger


def _serialize(course: Course) -> dict:
    return {
        "id":           course.id,
        "student_id":   course.student_id,
        "course_name":  course.course_name,
        "course_code":  course.course_code,
        "credit_hours": course.credit_hours,
        "grade":        course.grade,
        "semester":     course.semester,
        "created_at":   course.created_at.isoformat() if course.created_at else None,
        "updated_at":   course.updated_at.isoformat() if course.updated_at else None,
    }


def _get_student_or_404(db: Session, student_id: int) -> Student:
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student


def get_courses_for_student(db: Session, student_id: int) -> dict:
    """Return all courses for a student (cached)."""
    _get_student_or_404(db, student_id)

    cache_key = f"courses:student:{student_id}"
    cached = get_cache(cache_key)
    if cached:
        logger.info(f"Cache HIT — courses for student {student_id}")
        return cached

    courses = db.query(Course).filter(Course.student_id == student_id).all()
    result = {"total": len(courses), "courses": [_serialize(c) for c in courses]}
    set_cache(cache_key, result)
    logger.info(f"Cache MISS — fetched {len(courses)} courses for student {student_id}")
    return result


def get_course_by_id(db: Session, student_id: int, course_id: int) -> dict:
    """Return a single course that belongs to a specific student."""
    _get_student_or_404(db, student_id)

    cache_key = f"courses:{course_id}"
    cached = get_cache(cache_key)
    if cached:
        logger.info(f"Cache HIT — course {course_id}")
        return cached

    course = db.query(Course).filter(
        Course.id == course_id, Course.student_id == student_id
    ).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found for this student")

    result = _serialize(course)
    set_cache(cache_key, result)
    return result


def create_course(db: Session, student_id: int, data: CourseCreate, performed_by: str) -> Course:
    """Admin adds a course to a student."""
    _get_student_or_404(db, student_id)

    course = Course(student_id=student_id, **data.model_dump())
    db.add(course)
    db.commit()
    db.refresh(course)

    log = AuditLog(
        entity="course",
        entity_id=course.id,
        action="create",
        performed_by=performed_by,
        details=f"Added course {course.course_code} to student {student_id}",
    )
    db.add(log)
    db.commit()

    delete_pattern(f"courses:student:{student_id}")
    logger.info(f"Course {course.course_code} created for student {student_id} by {performed_by}")
    return course


def update_course(db: Session, student_id: int, course_id: int,
                  data: CourseUpdate, performed_by: str) -> Course:
    """Admin updates a course."""
    _get_student_or_404(db, student_id)

    course = db.query(Course).filter(
        Course.id == course_id, Course.student_id == student_id
    ).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found for this student")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(course, field, value)

    db.commit()
    db.refresh(course)

    log = AuditLog(
        entity="course",
        entity_id=course_id,
        action="update",
        performed_by=performed_by,
        details=str(data.model_dump(exclude_unset=True)),
    )
    db.add(log)
    db.commit()

    delete_cache(f"courses:{course_id}")
    delete_pattern(f"courses:student:{student_id}")
    logger.info(f"Course {course_id} updated by {performed_by}")
    return course


def delete_course(db: Session, student_id: int, course_id: int, performed_by: str) -> dict:
    """Admin deletes a course."""
    _get_student_or_404(db, student_id)

    course = db.query(Course).filter(
        Course.id == course_id, Course.student_id == student_id
    ).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found for this student")

    db.delete(course)

    log = AuditLog(
        entity="course",
        entity_id=course_id,
        action="delete",
        performed_by=performed_by,
        details=f"Deleted course {course.course_code} from student {student_id}",
    )
    db.add(log)
    db.commit()

    delete_cache(f"courses:{course_id}")
    delete_pattern(f"courses:student:{student_id}")
    logger.info(f"Course {course_id} deleted by {performed_by}")
    return {"message": "Course deleted successfully"}
