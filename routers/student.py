from fastapi import APIRouter, Depends, HTTPException,Query
from sqlalchemy.orm import Session

from auth import get_current_user, require_admin
from database import SessionLocal
from models import Student, User
from schemas import (StudentCreate,StudentResponse,StudentListResponse,MessageResponse)

router = APIRouter()

def get_db():

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()
def get_current_user_object(
        current_user: dict,
        db: Session
):
    user = db.query(User).filter(
        User.username == current_user["username"]
    ).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    return user
@router.get("/students",
            response_model=StudentListResponse)
def get_students(
        page:int = Query(1,ge=1),
        limit:int = Query(10,ge=1,le=100),
        search: str | None = Query(None,min_length=1,max_length=100),
        sort: str = Query("asc", pattern="^(asc|desc)$"),
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user)
):
    if current_user["role"] == "admin":
        query = db.query(Student)
    else:
        current_user_obj = get_current_user_object(
            current_user,
            db
        )

        query = db.query(Student).filter(
            Student.user_id == current_user_obj.id
        )
    if search:
        query = query.filter(
            Student.name.ilike(f"%{search}%")
        )
    if sort == "asc":
        query = query.order_by(Student.name.asc())
    else:
        query = query.order_by(Student.name.desc())
    total = query.count()
    skip = (page - 1) * limit
    students = query.offset(skip).limit(limit).all()
    return {
        "students": students,
        "page": page,
        "limit": limit,
        "total": total
    }

@router.post("/student",
             response_model=StudentResponse)
def add_student(
        student: StudentCreate,
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_admin)
):
    user = get_current_user_object(
        current_user,
        db
    )
    new_student = Student(
        name=student.name,
        user_id=user.id
    )

    db.add(new_student)

    db.commit()

    db.refresh(new_student)

    return {
        "id": new_student.id,
        "name": new_student.name,
        "user_id": new_student.user_id
    }
@router.put("/student/{id}",
            response_model=StudentResponse)
def update_student(
        id: int,
        student: StudentCreate,
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user)
):
    db_student = db.query(Student).filter(
        Student.id == id
    ).first()

    if not db_student:
        raise HTTPException(
            status_code=404,
            detail="Student not found"
        )

    current_user_obj = get_current_user_object(
        current_user,
        db
    )

    if (
            current_user["role"] != "admin"
            and db_student.user_id != current_user_obj.id
    ):
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to modify this student"
        )

    db_student.name = student.name

    db.commit()

    db.refresh(db_student)

    return db_student
@router.delete("/student/{id}",
               response_model=MessageResponse)
def delete_student(
        id: int,
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user)
):
    student = db.query(Student).filter(
        Student.id == id
    ).first()

    if not student:
        raise HTTPException(
            status_code=404,
            detail="Student not found"
        )

    current_user_obj = get_current_user_object(
        current_user,
        db
    )

    if (
            current_user["role"] != "admin"
            and student.user_id != current_user_obj.id
    ):
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to delete this student"
        )
    db.delete(student)
    db.commit()
    return {
        "message": "Student deleted successfully"
    }
@router.get("/student/{id}",
            response_model=StudentResponse)
def get_student(
        id: int,
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user)
):
    student = db.query(Student).filter(
        Student.id == id
    ).first()

    if not student:
        raise HTTPException(
            status_code=404,
            detail="Student not found"
        )
    current_user_obj = get_current_user_object(
        current_user,
        db
    )

    if (
            current_user["role"] != "admin"
            and student.user_id != current_user_obj.id
    ):
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to view this student"
        )

    return student
@router.get("/user/students",
            response_model=list[StudentResponse])
def get_user_students(
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    user = db.query(User).filter(
        User.username == current_user["username"]
    ).first()
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    return user.students