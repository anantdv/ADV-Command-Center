from datetime import datetime
from typing import Literal

from pydantic import Field

from app.schemas.common import CamelModel


class Course(CamelModel):
    id: str
    title: str
    module: str
    progress: int
    mandatory: bool
    duration: str


class TrainingResult(CamelModel):
    assessment_id: str
    score: float
    completed_at: datetime


class AssessmentSubmission(CamelModel):
    answers: dict[str, str | list[str]]


class TrainingOverview(CamelModel):
    courses: list[Course]
    badges: list[str]
    leaderboard: list[dict]
    results: list[TrainingResult]


class TrainingCourse(CamelModel):
    course_id: str
    title: str
    module: str | None = None
    description: str | None = None
    mandatory: bool = False
    passing_score: int = 70
    status: Literal["draft", "published", "archived"] = "draft"
    progress_percent: int | None = None


class TrainingCourseCreate(CamelModel):
    title: str
    module: str | None = None
    description: str | None = None
    mandatory: bool = False
    passing_score: int = Field(70, ge=1, le=100)
    status: Literal["draft", "published", "archived"] = "draft"
    source_id: str | None = None


class TrainingLesson(CamelModel):
    lesson_id: str
    course_id: str
    title: str
    lesson_type: Literal["text", "video", "pdf", "html"]
    content: str | None = None
    media_url: str | None = None
    duration_minutes: int | None = None
    sort_order: int = 0


class AssessmentQuestion(CamelModel):
    question_id: str
    question: str
    options: list[str]
    correct_answer: str | None = None
    explanation: str | None = None


class GenerateAssessmentRequest(CamelModel):
    source_id: str
    question_count: int = Field(5, ge=1, le=20)
    difficulty: Literal["basic", "intermediate", "advanced"] = "basic"


class GeneratedAssessment(CamelModel):
    assessment_id: str
    source_id: str
    questions: list[AssessmentQuestion]


class SubmitGeneratedAssessmentRequest(CamelModel):
    course_id: str
    assessment_id: str | None = None
    answers: dict[str, str]


class SubmitAssessmentRequest(SubmitGeneratedAssessmentRequest):
    """Public assessment submission contract."""


class DetailedTrainingResult(CamelModel):
    result_id: str
    course_id: str
    user: str
    score: int
    passed: bool
    badge_awarded: str | None = None
    completed_on: str
