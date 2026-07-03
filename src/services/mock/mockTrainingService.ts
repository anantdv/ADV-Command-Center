import { courses } from '../../data/mockData'
import type { SubmitAssessmentRequest, SubmitAssessmentResponse, TrainingResult } from '../../types/training'
import { mockDelay } from './mockUtils'
const results:TrainingResult[]=[{assessmentId:'selling-basics',score:94,completedAt:'2026-06-28T10:00:00Z'}]
export const mockTrainingService={getCourses:()=>mockDelay(courses),getResults:()=>mockDelay(results),getLeaderboard:()=>mockDelay([{rank:1,name:'Priya Shah',points:3480},{rank:2,name:'Admin User',points:2480}]),submitAssessment:(id:string,_request:SubmitAssessmentRequest):Promise<SubmitAssessmentResponse>=>mockDelay({assessmentId:id,score:88,completedAt:new Date().toISOString()})}
