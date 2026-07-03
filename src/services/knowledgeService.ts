import { apiClient } from './apiClient'
import { env } from '../config/env'
import type { KnowledgeSearchResult,KnowledgeSource,KnowledgeSourceCreate,RAGAnswer,RAGAnswerRequest } from '../types/knowledge'
export const knowledgeService={
  listSources:(status?:string)=>env.useMockApi?Promise.resolve([]):apiClient.get<KnowledgeSource[]>(`/api/knowledge/sources${status?`?status=${encodeURIComponent(status)}`:''}`),
  createSource:(request:KnowledgeSourceCreate)=>apiClient.post<KnowledgeSource>('/api/knowledge/sources',request),
  approveSource:(id:string)=>apiClient.post<KnowledgeSource>(`/api/knowledge/sources/${encodeURIComponent(id)}/approve`),
  ingestSource:(id:string)=>apiClient.post<{sourceId:string;chunkCount:number;indexed:boolean}>(`/api/knowledge/sources/${encodeURIComponent(id)}/ingest`),
  search:(query:string,module?:string)=>apiClient.post<KnowledgeSearchResult[]>('/api/knowledge/search',{query,module}),
  ask:(request:RAGAnswerRequest)=>env.useMockApi?Promise.resolve({answer:`No approved mock source is configured for “${request.question}”.`,citations:[],confidence:0,escalationRecommended:true,escalationReason:'No approved source found.'}):apiClient.post<RAGAnswer>('/api/knowledge/ask',request),
}
