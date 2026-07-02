from app.schemas.training import AssessmentSubmission, Course, TrainingOverview, TrainingResult
from app.utils.datetime import utc_now


class TrainingService:
    def __init__(self) -> None:
        self.courses = [
            Course(id="course-001", title="ERPNext Selling Basics", module="Selling", progress=72, mandatory=True, duration="1h 25m"),
            Course(id="course-002", title="Purchase Order Approval Process", module="Buying", progress=35, mandatory=True, duration="45m"),
            Course(id="course-003", title="Stock Reconciliation Training", module="Stock", progress=100, mandatory=False, duration="1h 10m"),
            Course(id="course-004", title="Accounts Receivable Management", module="Accounting", progress=58, mandatory=True, duration="55m"),
            Course(id="course-005", title="Project Task Management", module="Projects", progress=0, mandatory=False, duration="40m"),
        ]
        self.results = [TrainingResult(assessment_id="selling-basics", score=94, completed_at=utc_now())]

    async def list_courses(self) -> list[Course]: return self.courses
    async def list_results(self) -> list[TrainingResult]: return self.results

    async def submit(self, assessment_id: str, request: AssessmentSubmission) -> TrainingResult:
        del request
        result = TrainingResult(assessment_id=assessment_id, score=88, completed_at=utc_now())
        self.results.append(result)
        return result

    async def overview(self) -> TrainingOverview:
        return TrainingOverview(courses=self.courses, badges=["ERP Explorer", "Stock Specialist"], leaderboard=[{"rank":1,"name":"Priya Shah","points":3480}], results=self.results)


training_service = TrainingService()
