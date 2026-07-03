import { env } from '../config/env'
import type { Course, GeneratedAssessment, LeaderboardEntry, SubmitAssessmentRequest, SubmitAssessmentResponse, TrainingLesson, TrainingResult } from '../types/training'
import { apiClient } from './apiClient'
import { mockTrainingService } from './mock/mockTrainingService'
export const getTrainingCourses=():Promise<Course[]>=>env.useMockApi?mockTrainingService.getCourses():apiClient.get('/api/training/courses')
export const getTrainingResults=():Promise<TrainingResult[]>=>env.useMockApi?mockTrainingService.getResults():apiClient.get('/api/training/results')
export const submitAssessment=(id:string,request:SubmitAssessmentRequest):Promise<SubmitAssessmentResponse>=>env.useMockApi?mockTrainingService.submitAssessment(id,request):apiClient.post(`/api/training/assessments/${encodeURIComponent(id)}/submit`,request)
export const getTrainingLessons=(id:string):Promise<TrainingLesson[]>=>apiClient.get(`/api/training/courses/${encodeURIComponent(id)}/lessons`)
export const getTrainingLeaderboard=():Promise<LeaderboardEntry[]>=>env.useMockApi?mockTrainingService.getLeaderboard():apiClient.get('/api/training/leaderboard')
export const generateAssessment=(sourceId:string,questionCount=5):Promise<GeneratedAssessment>=>apiClient.post('/api/training/assessments/generate',{sourceId,questionCount,difficulty:'basic'})
