import { apiClient } from './apiClient'
import type { DocumentMappingPreview, DocumentUploadResponse, OCRResult, OcrExtractionDebug, IntakeSourceDocumentType } from '../types/documentIntake'

async function upload(file:File,sourceDocumentType:IntakeSourceDocumentType):Promise<DocumentUploadResponse>{
 const form=new FormData();form.append('file',file);form.append('source_document_type',sourceDocumentType)
 return apiClient.postForm<DocumentUploadResponse>('/api/document-intake/upload',form,120_000)
}

export const documentIntakeService={
 upload,
 process:(intakeId:string)=>apiClient.post<DocumentMappingPreview>(`/api/document-intake/${encodeURIComponent(intakeId)}/process`,undefined,120_000),
 getOcr:(intakeId:string)=>apiClient.get<OCRResult>(`/api/document-intake/${encodeURIComponent(intakeId)}/ocr`),
 getExtractionDebug:(intakeId:string)=>apiClient.get<OcrExtractionDebug>(`/api/document-intake/${encodeURIComponent(intakeId)}/extraction-debug`),
 getMappingPreview:(intakeId:string)=>apiClient.get<DocumentMappingPreview>(`/api/document-intake/${encodeURIComponent(intakeId)}/mapping-preview`),
 updateMappingPreview:(intakeId:string,request:{target_doctype:string;draft_payload:Record<string,unknown>})=>apiClient.put<DocumentMappingPreview>(`/api/document-intake/${encodeURIComponent(intakeId)}/mapping-preview`,request),
 confirmCreate:(intakeId:string)=>apiClient.post(`/api/document-intake/${encodeURIComponent(intakeId)}/confirm-create`),
 cancel:(intakeId:string)=>apiClient.post<boolean>(`/api/document-intake/${encodeURIComponent(intakeId)}/cancel`),
}
