from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select

from app.models import AcademicRecord, Attendance, Student
from app.routes.students import owned
from app.schemas import PredictionInput
from app.security import current_user, get_db
from app.services.analytics import student_report
from app.services.prediction import predict

router = APIRouter(tags=["Reports and predictions"])


@router.get("/reports/{student_id}")
def report(student_id: int, db=Depends(get_db), user=Depends(current_user)):
    owned(db, Student, student_id, user)
    return student_report(db, student_id)


@router.post("/predict")
def prediction(body: PredictionInput, request: Request, user=Depends(current_user)):
    return predict(request.app.state.model, body.model_dump())


@router.get("/predictions/{student_id}")
def student_prediction(student_id: int, request: Request, db=Depends(get_db), user=Depends(current_user)):
    owned(db, Student, student_id, user)
    records = db.scalars(select(AcademicRecord).where(AcademicRecord.student_id == student_id)).all()
    attendance = db.scalars(select(Attendance).where(Attendance.student_id == student_id)).all()
    if not records or not attendance:
        raise HTTPException(422, "Add attendance and academic records before predicting")
    latest_term = max(row.term for row in records)
    latest = [row for row in records if row.term == latest_term]
    features = {
        "attendance": 100 * sum(row.attended for row in attendance) / sum(row.total for row in attendance),
        "internal_marks": sum(row.internal_marks for row in latest) / len(latest),
        "assignment_score": sum(row.assignment_score for row in latest) / len(latest),
    }
    return {"student_id": student_id, "term": latest_term, "features": features,
            **predict(request.app.state.model, features)}
