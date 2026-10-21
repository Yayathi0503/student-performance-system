from datetime import date

from sqlalchemy import CheckConstraint, Date, Float, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(254), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))


class Student(Base):
    __tablename__ = "students"
    __table_args__ = (
        UniqueConstraint("owner_id", "registration_number"),
        UniqueConstraint("owner_id", "email"),
        CheckConstraint("semester BETWEEN 1 AND 12"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    registration_number: Mapped[str] = mapped_column(String(50))
    name: Mapped[str] = mapped_column(String(100))
    department: Mapped[str] = mapped_column(String(100))
    semester: Mapped[int]
    email: Mapped[str] = mapped_column(String(254))
    records: Mapped[list["AcademicRecord"]] = relationship(cascade="all, delete-orphan", passive_deletes=True)
    attendance: Mapped[list["Attendance"]] = relationship(cascade="all, delete-orphan", passive_deletes=True)


class Subject(Base):
    __tablename__ = "subjects"
    __table_args__ = (UniqueConstraint("owner_id", "code"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    code: Mapped[str] = mapped_column(String(30))
    name: Mapped[str] = mapped_column(String(100))


class Attendance(Base):
    __tablename__ = "attendance"
    __table_args__ = (
        UniqueConstraint("student_id", "subject_id", "date"),
        CheckConstraint("attended >= 0 AND total > 0 AND attended <= total"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), index=True)
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id"), index=True)
    date: Mapped[date] = mapped_column(Date)
    attended: Mapped[int]
    total: Mapped[int]


class AcademicRecord(Base):
    __tablename__ = "academic_records"
    __table_args__ = (
        UniqueConstraint("student_id", "subject_id", "term"),
        CheckConstraint("internal_marks BETWEEN 0 AND 100"),
        CheckConstraint("assignment_score BETWEEN 0 AND 100"),
        CheckConstraint("exam_marks BETWEEN 0 AND 100"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), index=True)
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id"), index=True)
    term: Mapped[int]
    internal_marks: Mapped[float] = mapped_column(Float)
    assignment_score: Mapped[float] = mapped_column(Float)
    exam_marks: Mapped[float] = mapped_column(Float)
