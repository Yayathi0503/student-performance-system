from datetime import date
from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

Score = Annotated[float, Field(ge=0, le=100, allow_inf_nan=False)]
Text = Annotated[str, Field(min_length=1, max_length=100)]


class Input(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid", from_attributes=True)


class Credentials(Input):
    model_config = ConfigDict(str_strip_whitespace=False)
    email: EmailStr = Field(max_length=254)
    password: str = Field(min_length=10, max_length=128)


class UserOut(Input):
    id: int
    email: EmailStr


class StudentInput(Input):
    registration_number: str = Field(min_length=1, max_length=50)
    name: Text
    department: Text
    semester: int = Field(ge=1, le=12)
    email: EmailStr = Field(max_length=254)


class StudentOut(StudentInput):
    id: int


class SubjectInput(Input):
    code: str = Field(min_length=1, max_length=30)
    name: Text


class SubjectOut(SubjectInput):
    id: int


class AttendanceInput(Input):
    student_id: int = Field(gt=0)
    subject_id: int = Field(gt=0)
    date: date
    attended: int = Field(ge=0, le=1000)
    total: int = Field(gt=0, le=1000)

    @model_validator(mode="after")
    def validate_counts(self):
        if self.attended > self.total:
            raise ValueError("Attended cannot exceed total classes")
        return self


class AttendanceOut(AttendanceInput):
    id: int


class RecordInput(Input):
    student_id: int = Field(gt=0)
    subject_id: int = Field(gt=0)
    term: int = Field(ge=1, le=12)
    internal_marks: Score
    assignment_score: Score
    exam_marks: Score


class RecordOut(RecordInput):
    id: int


class PredictionInput(Input):
    attendance: Score
    internal_marks: Score
    assignment_score: Score
