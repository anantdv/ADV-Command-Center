import { apiClient } from './apiClient'
import type { DocumentMappingPreview, DocumentUploadResponse, OCRResult } from '../types/documentIntake'

async function upload(file:File):Promise<DocumentUploadResponse>{
 const form=new FormData();form.append('file',file)
 return apiClient.postForm<DocumentUploadResponse>('/api/document-intake/upload',form)
}

export const documentIntakeService={
 upload,
 process:(intakeId:string)=>apiClient.post<DocumentMappingPreview>(`/api/document-intake/${encodeURIComponent(intakeId)}/process`),
 getOcr:(intakeId:string)=>apiClient.get<OCRResult>(`/api/document-intake/${encodeURIComponent(intakeId)}/ocr`),
 getMappingPreview:(intakeId:string)=>apiClient.get<DocumentMappingPreview>(`/api/document-intake/${encodeURIComponent(intakeId)}/mapping-preview`),
 updateMappingPreview:(intakeId:string,request:{target_doctype:string;draft_payload:Record<string,unknown>})=>apiClient.put<DocumentMappingPreview>(`/api/document-intake/${encodeURIComponent(intakeId)}/mapping-preview`,request),
 confirmCreate:(intakeId:string)=>apiClient.post(`/api/document-intake/${encodeURIComponent(intakeId)}/confirm-create`),
 cancel:(intakeId:string)=>apiClient.post<boolean>(`/api/document-intake/${encodeURIComponent(intakeId)}/cancel`),
}
