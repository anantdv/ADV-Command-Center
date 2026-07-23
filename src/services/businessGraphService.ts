import { apiClient } from './apiClient'
import type { BusinessTimeline, GraphNeighborhood, ReasoningRequest, ReasoningResponse, RelatedDocumentsResponse } from '../types/businessGraph'

export function getRelatedDocuments(doctype: string, name: string, depth = 1): Promise<RelatedDocumentsResponse> {
  return apiClient.get(`/api/business-graph/documents/${encodeURIComponent(doctype)}/${encodeURIComponent(name)}/related?depth=${depth}`)
}

export function getBusinessTimeline(doctype: string, name: string, depth = 2): Promise<BusinessTimeline> {
  return apiClient.get(`/api/business-graph/documents/${encodeURIComponent(doctype)}/${encodeURIComponent(name)}/timeline?depth=${depth}`)
}

export function traverseBusinessGraph(payload: { doctype: string; name: string; depth?: number; direction?: string; limit?: number }): Promise<GraphNeighborhood> {
  return apiClient.post('/api/business-graph/traverse', payload)
}

export function reasonAboutBusinessGraph(payload: ReasoningRequest): Promise<ReasoningResponse> {
  return apiClient.post('/api/business-graph/reason', payload)
}
