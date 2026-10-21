from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.models import Student, Subject
from app.schemas import StudentInput, StudentOut, SubjectInput, SubjectOut
from app.security import current_user, get_db

router = APIRouter(tags=["Students and subjects"])


def owned(db, model, item_id, user):
    item = db.scalar(select(model).where(model.id == item_id, model.owner_id == user.id))
    if item is None:
        raise HTTPException(404, "Record not found")
    return item


def commit(db):
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Duplicate record or record still referenced")


@router.post("/students", response_model=StudentOut, status_code=201)
def create_student(body: StudentInput, db=Depends(get_db), user=Depends(current_user)):
    student = Student(owner_id=user.id, **body.model_dump())
    db.add(student)
    commit(db)
    return student


@router.get("/students", response_model=list[StudentOut])
def students(offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=100),
             db=Depends(get_db), user=Depends(current_user)):
    return db.scalars(select(Student).where(Student.owner_id == user.id).order_by(Student.id).offset(offset).limit(limit)).all()


@router.get("/students/{student_id}", response_model=StudentOut)
def student(student_id: int, db=Depends(get_db), user=Depends(current_user)):
    return owned(db, Student, student_id, user)


@router.put("/students/{student_id}", response_model=StudentOut)
def update_student(student_id: int, body: StudentInput, db=Depends(get_db), user=Depends(current_user)):
    row = owned(db, Student, student_id, user)
    for key, value in body.model_dump().items():
        setattr(row, key, value)
    commit(db)
    return row


@router.delete("/students/{student_id}", status_code=204)
def delete_student(student_id: int, db=Depends(get_db), user=Depends(current_user)):
    db.delete(owned(db, Student, student_id, user))
    commit(db)
    return Response(status_code=204)


@router.post("/subjects", response_model=SubjectOut, status_code=201)
def create_subject(body: SubjectInput, db=Depends(get_db), user=Depends(current_user)):
    row = Subject(owner_id=user.id, **body.model_dump())
    db.add(row)
    commit(db)
    return row


@router.get("/subjects", response_model=list[SubjectOut])
def subjects(offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=100),
             db=Depends(get_db), user=Depends(current_user)):
    return db.scalars(select(Subject).where(Subject.owner_id == user.id).order_by(Subject.id).offset(offset).limit(limit)).all()


@router.get("/subjects/{subject_id}", response_model=SubjectOut)
def subject(subject_id: int, db=Depends(get_db), user=Depends(current_user)):
    return owned(db, Subject, subject_id, user)


@router.put("/subjects/{subject_id}", response_model=SubjectOut)
def update_subject(subject_id: int, body: SubjectInput, db=Depends(get_db), user=Depends(current_user)):
    row = owned(db, Subject, subject_id, user)
    for key, value in body.model_dump().items():
        setattr(row, key, value)
    commit(db)
    return row


@router.delete("/subjects/{subject_id}", status_code=204)
def delete_subject(subject_id: int, db=Depends(get_db), user=Depends(current_user)):
    db.delete(owned(db, Subject, subject_id, user))
    commit(db)
    return Response(status_code=204)
