import { courses } from '../../data/mockData'
import type { SubmitAssessmentRequest, SubmitAssessmentResponse, TrainingResult } from '../../types/training'
import { mockDelay } from './mockUtils'
const results:TrainingResult[]=[{assessmentId:'selling-basics',score:94,completedAt:'2026-06-28T10:00:00Z'}]
export const mockTrainingService={getCourses:()=>mockDelay(courses),getResults:()=>mockDelay(results),submitAssessment:(id:string,_request:SubmitAssessmentRequest):Promise<SubmitAssessmentResponse>=>mockDelay({assessmentId:id,score:88,completedAt:new Date().toISOString()})}
