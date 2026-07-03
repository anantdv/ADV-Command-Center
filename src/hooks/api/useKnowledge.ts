import { useMutation,useQuery,useQueryClient } from '@tanstack/react-query'
import { knowledgeService } from '../../services/knowledgeService'
export const knowledgeKeys={sources:['knowledge','sources'] as const}
export const useKnowledgeSources=()=>useQuery({queryKey:knowledgeKeys.sources,queryFn:()=>knowledgeService.listSources()})
export const useAskKnowledge=()=>useMutation({mutationFn:knowledgeService.ask})
export const useCreateKnowledgeSource=()=>{const client=useQueryClient();return useMutation({mutationFn:knowledgeService.createSource,onSuccess:()=>client.invalidateQueries({queryKey:knowledgeKeys.sources})})}
export const useApproveKnowledgeSource=()=>{const client=useQueryClient();return useMutation({mutationFn:knowledgeService.approveSource,onSuccess:()=>client.invalidateQueries({queryKey:knowledgeKeys.sources})})}
export const useIngestKnowledgeSource=()=>useMutation({mutationFn:knowledgeService.ingestSource})
