import { useMutation } from '@tanstack/react-query'
import { documentIntakeService } from '../../services/documentIntakeService'

export function useDocumentUpload(){return useMutation({mutationFn:(file:File)=>documentIntakeService.upload(file)})}
export function useProcessDocument(){return useMutation({mutationFn:(intakeId:string)=>documentIntakeService.process(intakeId)})}
export function useConfirmDocumentDraft(){return useMutation({mutationFn:(intakeId:string)=>documentIntakeService.confirmCreate(intakeId)})}
