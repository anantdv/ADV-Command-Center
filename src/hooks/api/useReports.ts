import { useMutation, useQuery } from '@tanstack/react-query'
import { reportService } from '../../services/reportService'
import type { ReportRunWithColumnsRequest } from '../../types/reportBuilder'

export function useAvailableColumns(sourceType:'doctype'|'report',sourceName:string,enabled=true){
  return useQuery({queryKey:['reports','columns',sourceType,sourceName],queryFn:()=>reportService.availableColumns(sourceType,sourceName),enabled:enabled&&!!sourceName})
}

export function useRunReportWithColumns(){
  return useMutation({mutationFn:(payload:ReportRunWithColumnsRequest)=>reportService.runWithColumns(payload)})
}

export function useReportDiagnostic(reportName:string,enabled=false){
  return useQuery({queryKey:['reports','diagnose',reportName],queryFn:()=>reportService.diagnose(reportName),enabled:enabled&&!!reportName})
}
