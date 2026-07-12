import { env } from '../config/env'
import type { CreateDashboardWidgetRequest, DashboardOverviewResponse, DashboardWidgetData, DashboardWidgetLayout, PinChatResultRequest, PinChatResultResponse, UpdateDashboardWidgetRequest } from '../types/dashboard'
import type { AppDateRange } from '../types/dateRange'
import { apiClient } from './apiClient'
import { mockDashboardService } from './mock/mockDashboardService'

const dateRangeQuery = (range?: AppDateRange) => {
  if (!range) return ''
  const params = new URLSearchParams({ from_date: range.from, to_date: range.to })
  return `?${params.toString()}`
}

export const getDashboardOverview=(range?:AppDateRange):Promise<DashboardOverviewResponse>=>env.useMockApi?mockDashboardService.getDashboardOverview():apiClient.get(`/api/dashboard/overview${dateRangeQuery(range)}`)
export const getDashboardWidgets=():Promise<DashboardWidgetData[]>=>env.useMockApi?mockDashboardService.getDashboardWidgets():apiClient.get('/api/dashboard/widgets')
export const createDashboardWidget=(request:CreateDashboardWidgetRequest):Promise<DashboardWidgetData>=>env.useMockApi?mockDashboardService.createDashboardWidget(request):apiClient.post('/api/dashboard/widgets',request)
export const refreshDashboardWidget=(id:string):Promise<DashboardWidgetData>=>env.useMockApi?mockDashboardService.refreshDashboardWidget(id):apiClient.post(`/api/dashboard/widgets/${encodeURIComponent(id)}/refresh`)
export const updateDashboardWidget=({id,request}:{id:string;request:UpdateDashboardWidgetRequest}):Promise<DashboardWidgetData>=>env.useMockApi?mockDashboardService.updateDashboardWidget(id,request):apiClient.put(`/api/dashboard/widgets/${encodeURIComponent(id)}`,request)
export const deleteDashboardWidget=(id:string):Promise<boolean>=>env.useMockApi?mockDashboardService.deleteDashboardWidget(id):apiClient.delete(`/api/dashboard/widgets/${encodeURIComponent(id)}`)
export const reorderDashboardWidgets=(layouts:Array<{widget_id:string;layout:DashboardWidgetLayout}>):Promise<boolean>=>env.useMockApi?mockDashboardService.reorderDashboardWidgets(layouts):apiClient.post('/api/dashboard/widgets/reorder',{layouts})
export const pinChatResultToDashboard=(request:PinChatResultRequest):Promise<PinChatResultResponse>=>env.useMockApi?mockDashboardService.pinChatResultToDashboard(request):apiClient.post('/api/chat/actions/pin-to-dashboard',request)
