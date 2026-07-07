import { env } from '../config/env'
import { apiClient } from './apiClient'
import type { DocumentMappingPreview, DocumentUploadResponse, OCRResult } from '../types/documentIntake'

async function upload(file:File):Promise<DocumentUploadResponse>{
 const form=new FormData();form.append('file',file)
 const response=await fetch(`${env.apiBaseUrl}/api/document-intake/upload`,{method:'POST',body:form,credentials:'include',headers:{Accept:'application/json'}})
 const payload=await response.json()
 if(!response.ok||payload.success===false)throw new Error(payload.message||'Upload failed')
 return payload.data
}

export const documentIntakeService={
 upload,
 process:(intakeId:string)=>apiClient.post<DocumentMappingPreview>(`/api/document-intake/${intakeId}/process`),
 getOcr:(intakeId:string)=>apiClient.get<OCRResult>(`/api/document-intake/${intakeId}/ocr`),
 getMappingPreview:(intakeId:string)=>apiClient.get<DocumentMappingPreview>(`/api/document-intake/${intakeId}/mapping-preview`),
 confirmCreate:(intakeId:string)=>apiClient.post(`/api/document-intake/${intakeId}/confirm-create`),
 cancel:(intakeId:string)=>apiClient.post<boolean>(`/api/document-intake/${intakeId}/cancel`),
}
