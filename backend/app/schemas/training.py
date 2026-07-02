from datetime import datetime

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
