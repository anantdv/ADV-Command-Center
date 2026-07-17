import { apiClient } from './apiClient'
import type { AnalyticsDefinition, AnalyticsResult, AnalyticsRunRequest } from '../types/analytics'

export const analyticsService={
  catalog:async(module?:string)=>Object.values(await apiClient.get<Record<string,AnalyticsDefinition>>(`/api/analytics/catalog${module?`?module=${encodeURIComponent(module)}`:''}`)),
  get:(analyticsKey:string)=>apiClient.get<AnalyticsDefinition>(`/api/analytics/${encodeURIComponent(analyticsKey)}`),
  run:(request:AnalyticsRunRequest)=>apiClient.post<AnalyticsResult>('/api/analytics/run',request),
  runByKey:(analyticsKey:string,request:Omit<AnalyticsRunRequest,'analyticsKey'|'analytics_key'>={})=>apiClient.post<AnalyticsResult>(`/api/analytics/${encodeURIComponent(analyticsKey)}/run`,request),
}
