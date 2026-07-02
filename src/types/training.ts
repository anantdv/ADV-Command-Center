export type Course = { id: string; title: string; module: string; progress: number; mandatory: boolean; duration: string }
export type TrainingData = { courses: Course[] }
export type TrainingResult = { assessmentId: string; score: number; completedAt: string }
export type SubmitAssessmentRequest = { answers: Record<string, string | string[]> }
export type SubmitAssessmentResponse = TrainingResult
