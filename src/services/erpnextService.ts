import { env } from '../config/env'
import type { AllowedDoctype, DoctypeSchemaRequest, DoctypeSchemaResponse, ErpnextUserContext, GetRecordRequest, ListRecordsRequest, ListRecordsResponse, RecordResponse } from '../types/erpnext'
import { apiClient } from './apiClient'
import { mockErpnextService } from './mock/mockErpnextService'
export const getCurrentUserContext=():Promise<ErpnextUserContext>=>env.useMockApi?mockErpnextService.getCurrentUserContext():apiClient.get('/api/erpnext/current-user-context')
export const getAllowedDoctypes=():Promise<AllowedDoctype[]>=>env.useMockApi?mockErpnextService.getAllowedDoctypes():apiClient.get('/api/erpnext/allowed-doctypes')
export const getDoctypeSchema=(request:DoctypeSchemaRequest):Promise<DoctypeSchemaResponse>=>env.useMockApi?mockErpnextService.getDoctypeSchema(request):apiClient.post('/api/erpnext/doctype-schema',request)
export const listRecords=(request:ListRecordsRequest):Promise<ListRecordsResponse>=>env.useMockApi?mockErpnextService.listRecords(request):apiClient.post('/api/erpnext/list-records',request)
export const getRecord=(request:GetRecordRequest):Promise<RecordResponse>=>env.useMockApi?mockErpnextService.getRecord(request):apiClient.post('/api/erpnext/get-record',request)
// Business record mutations intentionally live only in the Command Center
// confirmation workflow. Do not add direct create/update calls here.
