from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import select

from app.models import AcademicRecord, Attendance, Student, Subject
from app.routes.students import commit, owned
from app.schemas import AttendanceInput, AttendanceOut, RecordInput, RecordOut
from app.security import current_user, get_db

router = APIRouter(tags=["Academic records"])


def check_links(db, body, user):
    owned(db, Student, body.student_id, user)
    owned(db, Subject, body.subject_id, user)


def owned_record(db, model, record_id, user):
    row = db.scalar(select(model).join(Student).where(model.id == record_id, Student.owner_id == user.id))
    if row is None:
        raise HTTPException(404, "Record not found")
    return row


@router.post("/attendance", response_model=AttendanceOut, status_code=201)
def add_attendance(body: AttendanceInput, db=Depends(get_db), user=Depends(current_user)):
    check_links(db, body, user)
    row = Attendance(**body.model_dump())
    db.add(row)
    commit(db)
    return row


@router.get("/attendance", response_model=list[AttendanceOut])
def list_attendance(student_id: int, offset: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500),
                    db=Depends(get_db), user=Depends(current_user)):
    owned(db, Student, student_id, user)
    return db.scalars(select(Attendance).where(Attendance.student_id == student_id).order_by(Attendance.date, Attendance.id).offset(offset).limit(limit)).all()


@router.put("/attendance/{record_id}", response_model=AttendanceOut)
def update_attendance(record_id: int, body: AttendanceInput, db=Depends(get_db), user=Depends(current_user)):
    row = owned_record(db, Attendance, record_id, user)
    check_links(db, body, user)
    for key, value in body.model_dump().items():
        setattr(row, key, value)
    commit(db)
    return row


@router.delete("/attendance/{record_id}", status_code=204)
def delete_attendance(record_id: int, db=Depends(get_db), user=Depends(current_user)):
    db.delete(owned_record(db, Attendance, record_id, user))
    commit(db)
    return Response(status_code=204)


@router.post("/academic-records", response_model=RecordOut, status_code=201)
def add_record(body: RecordInput, db=Depends(get_db), user=Depends(current_user)):
    check_links(db, body, user)
    row = AcademicRecord(**body.model_dump())
    db.add(row)
    commit(db)
    return row


@router.get("/academic-records", response_model=list[RecordOut])
def list_records(student_id: int, offset: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500),
                 db=Depends(get_db), user=Depends(current_user)):
    owned(db, Student, student_id, user)
    return db.scalars(select(AcademicRecord).where(AcademicRecord.student_id == student_id).order_by(AcademicRecord.term, AcademicRecord.id).offset(offset).limit(limit)).all()


@router.put("/academic-records/{record_id}", response_model=RecordOut)
def update_record(record_id: int, body: RecordInput, db=Depends(get_db), user=Depends(current_user)):
    row = owned_record(db, AcademicRecord, record_id, user)
    check_links(db, body, user)
    for key, value in body.model_dump().items():
        setattr(row, key, value)
    commit(db)
    return row


@router.delete("/academic-records/{record_id}", status_code=204)
def delete_record(record_id: int, db=Depends(get_db), user=Depends(current_user)):
    db.delete(owned_record(db, AcademicRecord, record_id, user))
    commit(db)
    return Response(status_code=204)
