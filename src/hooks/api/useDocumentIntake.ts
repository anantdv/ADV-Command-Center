import { useMutation } from '@tanstack/react-query'
import { documentIntakeService } from '../../services/documentIntakeService'
import type { IntakeSourceDocumentType } from '../../types/documentIntake'

export function useDocumentUpload(){return useMutation({mutationFn:({file,sourceDocumentType}:{file:File;sourceDocumentType:IntakeSourceDocumentType})=>documentIntakeService.upload(file,sourceDocumentType)})}
export function useProcessDocument(){return useMutation({mutationFn:async(intakeId:string)=>{await documentIntakeService.process(intakeId);return documentIntakeService.getMappingPreview(intakeId)}})}
export function useConfirmDocumentDraft(){return useMutation({mutationFn:(intakeId:string)=>documentIntakeService.confirmCreate(intakeId)})}
