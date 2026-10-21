import pandas as pd
from sqlalchemy import select

from app.models import AcademicRecord, Attendance, Subject


def student_report(db, student_id):
    records = db.execute(select(AcademicRecord, Subject.name).join(Subject).where(AcademicRecord.student_id == student_id)).all()
    attendance = db.scalars(select(Attendance).where(Attendance.student_id == student_id)).all()
    total = sum(row.total for row in attendance)
    percentage = round(100 * sum(row.attended for row in attendance) / total, 2) if total else None
    result = {"student_id": student_id, "attendance_percentage": percentage,
              "overall_average": None, "subjects": [], "terms": [], "trend": "insufficient_data"}
    if not records:
        return result
    frame = pd.DataFrame([{"subject_id": row.subject_id, "subject": name, "term": row.term,
                           "internal_marks": row.internal_marks, "assignment_score": row.assignment_score,
                           "exam_marks": row.exam_marks} for row, name in records])
    # Each component and each recorded subject-term has equal weight.
    frame["average"] = frame[["internal_marks", "assignment_score", "exam_marks"]].mean(axis=1)
    result["overall_average"] = round(float(frame["average"].mean()), 2)
    result["subjects"] = frame.groupby(["subject_id", "subject"], as_index=False)["average"].mean().round(2).to_dict("records")
    terms = frame.groupby("term", as_index=False)["average"].mean().sort_values("term").round(2)
    result["terms"] = terms.to_dict("records")
    if len(terms) >= 2:
        change = float(terms.iloc[-1]["average"] - terms.iloc[-2]["average"])
        result["trend"] = "improving" if change > 0 else "declining" if change < 0 else "stable"
    return result
