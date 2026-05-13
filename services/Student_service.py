from sqlalchemy.orm import Session
from fastapi import HTTPException
from App.Models.Student import Student
from App.Models.User import User, RoleEnum
from App.Schemas.Student import StudentCreate, StudentUpdate
from App.Auth.Password import hash_password
from App.Utils.Cache import get_cache, set_cache, delete_cache, delete_pattern
from App.Utils.Logger import logger
from App.Models.AuditLog import AuditLog

def _serialize(student: Student) -> dict:
    return {
        "id": student.id,
        "full_name": student.full_name,
        "email": student.email,
        "department": student.department,
        "gpa": student.gpa,
        "phone": student.phone,
        "user_id": student.user_id,
        "created_at": student.created_at.isoformat() if student.created_at else None,
        "updated_at": student.updated_at.isoformat() if student.updated_at else None,
    }

def get_all_students(db: Session, department=None, min_gpa=None, page=1, size=10):
    cache_key = f"students:all:{department}:{min_gpa}:{page}:{size}"
    cached = get_cache(cache_key)
    if cached:
        logger.info("Cache HIT for all students")
        return cached
    query = db.query(Student)
    if department:
        query = query.filter(Student.department == department)
    if min_gpa is not None:
        query = query.filter(Student.gpa >= min_gpa)
    total = query.count()
    students = query.order_by(Student.id).offset((page - 1) * size).limit(size).all()
    result = {"total": total, "page": page, "size": size, "students": [_serialize(s) for s in students]}
    set_cache(cache_key, result)
    logger.info(f"Cache MISS — fetched {len(students)} students from DB")
    return result

def get_student_by_id(db: Session, student_id: int) -> dict:
    cache_key = f"students:{student_id}"
    cached = get_cache(cache_key)
    if cached:
        logger.info(f"Cache HIT for student {student_id}")
        return cached
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    result = _serialize(student)
    set_cache(cache_key, result)
    return result

def get_student_by_user_id(db: Session, user_id: int) -> dict:
    cache_key = f"students:user:{user_id}"
    cached = get_cache(cache_key)
    if cached:
        logger.info(f"Cache HIT for student user_id={user_id}")
        return cached
    student = db.query(Student).filter(Student.user_id == user_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="No student profile found for your account.")
    result = _serialize(student)
    set_cache(cache_key, result)
    return result

def create_student(db: Session, student_data: StudentCreate) -> Student:
    if db.query(User).filter(User.email == student_data.email).first():
        raise HTTPException(status_code=400, detail="A user with this email already exists")
    if db.query(Student).filter(Student.email == student_data.email).first():
        raise HTTPException(status_code=400, detail="A student with this email already exists")
    if student_data.phone and db.query(Student).filter(Student.phone == student_data.phone).first():
        raise HTTPException(status_code=400, detail="This phone number is already used by another student")

    user = User(email=student_data.email, hashed_password=hash_password(student_data.password), role=RoleEnum.student)
    db.add(user)
    db.flush()

    student = Student(user_id=user.id, full_name=student_data.full_name, email=student_data.email,
                      department=student_data.department, gpa=student_data.gpa, phone=student_data.phone)
    db.add(student)
    db.commit()
    db.refresh(student)

    db.add(AuditLog(entity="student", entity_id=student.id, action="create",
                    performed_by="admin", details=f"Created {student.full_name} user_id={user.id}"))
    db.commit()

    delete_pattern("students:all:*")
    logger.info(f"Admin created student: {student.full_name} (user_id={user.id})")
    return student

def update_student(db: Session, student_id: int, update_data: StudentUpdate, updated_by: str) -> Student:
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    update_dict = update_data.model_dump(exclude_unset=True)

    if "password" in update_dict:
        user = db.query(User).filter(User.id == student.user_id).first()
        if user:
            user.hashed_password = hash_password(update_dict.pop("password"))

    if "email" in update_dict:
        new_email = update_dict["email"]
        if db.query(Student).filter(Student.email == new_email, Student.id != student_id).first():
            raise HTTPException(status_code=400, detail="Email already used by another student")
        if db.query(User).filter(User.email == new_email, User.id != student.user_id).first():
            raise HTTPException(status_code=400, detail="Email already registered to another account")
        user = db.query(User).filter(User.id == student.user_id).first()
        if user:
            user.email = new_email

    if "phone" in update_dict and update_dict["phone"]:
        if db.query(Student).filter(Student.phone == update_dict["phone"], Student.id != student_id).first():
            raise HTTPException(status_code=400, detail="Phone already used by another student")

    for field, value in update_dict.items():
        setattr(student, field, value)

    db.commit()
    db.refresh(student)

    db.add(AuditLog(entity="student", entity_id=student_id, action="update",
                    performed_by=updated_by, details=str(update_data.model_dump(exclude_unset=True))))
    db.commit()

    delete_cache(f"students:{student_id}")
    delete_cache(f"students:user:{student.user_id}")
    delete_pattern("students:all:*")
    logger.info(f"Student {student_id} updated by {updated_by}")
    return student

def delete_student(db: Session, student_id: int, performed_by: str = "admin") -> dict:
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    user_id = student.user_id
    student_name = student.full_name
    db.delete(student)

    user = db.query(User).filter(User.id == user_id).first()
    if user:
        db.delete(user)

    db.add(AuditLog(entity="student", entity_id=student_id, action="delete",
                    performed_by=performed_by, details=f"Deleted {student_name} and user {user_id}"))
    db.commit()

    delete_cache(f"students:{student_id}")
    delete_cache(f"students:user:{user_id}")
    delete_pattern("students:all:*")
    logger.info(f"Deleted student {student_id} by {performed_by}")
    return {"message": "Student deleted successfully"}
