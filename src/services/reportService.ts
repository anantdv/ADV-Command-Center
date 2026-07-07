import { apiClient } from './apiClient'
import type { ReportColumn, ReportDiagnosticResponse, ReportRunWithColumnsRequest, ReportRunWithColumnsResponse } from '../types/reportBuilder'

export const reportService={
  availableColumns:(sourceType:'doctype'|'report',sourceName:string)=>apiClient.get<ReportColumn[]>(`/api/reports/available-columns?source_type=${encodeURIComponent(sourceType)}&source_name=${encodeURIComponent(sourceName)}`),
  runWithColumns:(payload:ReportRunWithColumnsRequest)=>apiClient.post<ReportRunWithColumnsResponse>('/api/reports/run-with-columns',payload),
  diagnose:(reportName:string,filters:Record<string,unknown>={})=>apiClient.post<ReportDiagnosticResponse>('/api/reports/diagnose',{report_name:reportName,filters}),
}
