import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { generateAssessment, getTrainingCourses, getTrainingLeaderboard, getTrainingResults, submitAssessment } from '../../services/trainingService'
import type { SubmitAssessmentRequest } from '../../types/training'
export const trainingKeys={courses:['training','courses'] as const,results:['training','results'] as const}
export const useTrainingCourses=()=>useQuery({queryKey:trainingKeys.courses,queryFn:getTrainingCourses})
export const useTrainingResults=()=>useQuery({queryKey:trainingKeys.results,queryFn:getTrainingResults})
export function useSubmitAssessment(){const client=useQueryClient();return useMutation({mutationFn:({id,request}:{id:string;request:SubmitAssessmentRequest})=>submitAssessment(id,request),onSuccess:()=>client.invalidateQueries({queryKey:trainingKeys.results})})}
export const useTrainingLeaderboard=()=>useQuery({queryKey:['training','leaderboard'],queryFn:getTrainingLeaderboard})
export const useGenerateAssessment=()=>useMutation({mutationFn:({sourceId,count}:{sourceId:string;count?:number})=>generateAssessment(sourceId,count)})
