import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { createDashboardWidget, deleteDashboardWidget, getDashboardOverview, getDashboardWidgets, pinChatResultToDashboard, refreshDashboardWidget, reorderDashboardWidgets, updateDashboardWidget } from '../../services/dashboardService'
import { useAppStore } from '../../store/useAppStore'
export const dashboardKeys={all:['dashboard'] as const,overview:(from?:string,to?:string)=>['dashboard','overview',from||'',to||''] as const,widgets:['dashboard','widgets'] as const}
const invalidate=(client:ReturnType<typeof useQueryClient>)=>Promise.all([client.invalidateQueries({queryKey:['dashboard','overview']}),client.invalidateQueries({queryKey:dashboardKeys.widgets})])
export const useDashboardOverview=()=>{const range=useAppStore(state=>state.dateRange);return useQuery({queryKey:dashboardKeys.overview(range.from,range.to),queryFn:()=>getDashboardOverview(range)})}
export const useDashboardWidgets=()=>useQuery({queryKey:dashboardKeys.widgets,queryFn:getDashboardWidgets})
export function useCreateDashboardWidget(){const client=useQueryClient();return useMutation({mutationFn:createDashboardWidget,onSuccess:()=>invalidate(client)})}
export function useRefreshDashboardWidget(){const client=useQueryClient();return useMutation({mutationFn:refreshDashboardWidget,onSuccess:()=>invalidate(client)})}
export function useUpdateDashboardWidget(){const client=useQueryClient();return useMutation({mutationFn:updateDashboardWidget,onSuccess:()=>invalidate(client)})}
export function useDeleteDashboardWidget(){const client=useQueryClient();return useMutation({mutationFn:deleteDashboardWidget,onSuccess:()=>invalidate(client)})}
export function useReorderDashboardWidgets(){const client=useQueryClient();return useMutation({mutationFn:reorderDashboardWidgets,onSuccess:()=>invalidate(client)})}
export function usePinChatResultToDashboard(){const client=useQueryClient();return useMutation({mutationFn:pinChatResultToDashboard,onSuccess:()=>invalidate(client)})}
