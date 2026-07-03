from app.agents.training_agent import TrainingAgent
from app.core.audit import AuditEvent, log_audit_event
from app.core.exceptions import AppError
from app.schemas.training import AssessmentSubmission, Course, DetailedTrainingResult, GenerateAssessmentRequest, GeneratedAssessment, TrainingCourse, TrainingCourseCreate, TrainingLesson, TrainingOverview, TrainingResult
from app.utils.datetime import utc_now
from app.utils.ids import new_id


class TrainingService:
    def __init__(self) -> None:
        self.courses=[Course(id="course-001",title="ERPNext Selling Basics",module="Selling",progress=72,mandatory=True,duration="1h 25m"),Course(id="course-002",title="Purchase Order Approval Process",module="Buying",progress=35,mandatory=True,duration="45m"),Course(id="course-003",title="Stock Reconciliation Training",module="Stock",progress=100,mandatory=False,duration="1h 10m"),Course(id="course-004",title="Accounts Receivable Management",module="Accounting",progress=58,mandatory=True,duration="55m"),Course(id="course-005",title="Project Task Management",module="Projects",progress=0,mandatory=False,duration="40m")]
        self.results=[TrainingResult(assessment_id="selling-basics",score=94,completed_at=utc_now())]
        self.lessons=[TrainingLesson(lesson_id="lesson-001",course_id="course-001",title="Selling workflow",lesson_type="text",content="Understand the quotation to invoice workflow.",duration_minutes=15,sort_order=1)]
        self.assessments: dict[str,GeneratedAssessment]={}
        self.detailed_results: list[DetailedTrainingResult]=[]
        self.agent=TrainingAgent()

    async def list_courses(self)->list[Course]: return self.courses
    async def create_course(self,request:TrainingCourseCreate,user_roles:list[str]|None=None)->TrainingCourse:
        if request.source_id:
            from app.services.knowledge_service import knowledge_service
            source=await knowledge_service.get_source(request.source_id,user_roles or [])
            if source.status!="approved": raise AppError("Training courses can only be created from approved sources.",409)
        values=request.model_dump(exclude={"source_id"})
        course=TrainingCourse(course_id=new_id("course"),progress_percent=0,**values);self.courses.append(Course(id=course.course_id,title=course.title,module=course.module or "General",progress=0,mandatory=course.mandatory,duration="Self-paced"));return course
    async def get_course(self,course_id:str)->TrainingCourse:
        item=next((course for course in self.courses if course.id==course_id),None)
        if not item: raise AppError("Training course not found.",404)
        return TrainingCourse(course_id=item.id,title=item.title,module=item.module,mandatory=item.mandatory,status="published",progress_percent=item.progress)
    async def list_lessons(self,course_id:str)->list[TrainingLesson]: return sorted([item for item in self.lessons if item.course_id==course_id],key=lambda item:item.sort_order)
    async def list_results(self): return [*self.results,*self.detailed_results]
    async def generate_assessment(self,request:GenerateAssessmentRequest,user:str,roles:list[str])->GeneratedAssessment:
        assessment=await self.agent.generate_assessment(request,user,roles);self.assessments[assessment.assessment_id]=assessment;return GeneratedAssessment(assessment_id=assessment.assessment_id,source_id=assessment.source_id,questions=[question.model_copy(update={"correct_answer":None,"explanation":None}) for question in assessment.questions])
    async def submit(self,assessment_id:str,request:AssessmentSubmission,user:str="unknown"):
        generated=self.assessments.get(assessment_id)
        if not generated:
            result=TrainingResult(assessment_id=assessment_id,score=88,completed_at=utc_now());self.results.append(result);return result
        answers={key:str(value) for key,value in request.answers.items()}
        correct=sum(1 for question in generated.questions if answers.get(question.question_id)==question.correct_answer)
        score=round(correct/max(len(generated.questions),1)*100)
        result=DetailedTrainingResult(result_id=new_id("result"),course_id=generated.source_id,user=user,score=score,passed=score>=70,badge_awarded="Knowledge Champion" if score>=90 else None,completed_on=utc_now().isoformat());self.detailed_results.append(result)
        await log_audit_event(AuditEvent(user=user,action="training_assessment_submitted",agent_name="training_service",allowed=True,risk_level="low",source_id=generated.source_id,record_count=len(generated.questions),status="passed" if result.passed else "failed",erp_data_sent=False))
        if result.passed:
            await log_audit_event(AuditEvent(user=user,action="training_course_completed",agent_name="training_service",allowed=True,risk_level="low",source_id=generated.source_id,status="completed",erp_data_sent=False))
        return result
    async def overview(self)->TrainingOverview: return TrainingOverview(courses=self.courses,badges=["ERP Explorer","Stock Specialist"],leaderboard=await self.leaderboard(),results=self.results)
    async def leaderboard(self)->list[dict]: return [{"rank":1,"name":"Priya Shah","points":3480},{"rank":2,"name":"Admin User","points":2480}]


training_service=TrainingService()
