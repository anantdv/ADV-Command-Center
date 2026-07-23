export type GraphNodeType = 'document' | 'master' | 'transaction' | 'child_row' | 'system'
export type GraphEdgeType = 'LINKS_TO' | 'CONTAINS' | 'PARENT_OF' | 'GENERATED' | 'PAID_BY' | 'POSTED_TO' | 'ASSIGNED_TO' | 'RELATED_TO' | 'BLOCKED_BY' | 'DEPENDS_ON'

export interface GraphNode {
  id: string
  doctype: string
  name: string
  label?: string | null
  node_type: GraphNodeType
  nodeType?: GraphNodeType
  status?: string | null
  metadata: Record<string, unknown>
}

export interface GraphEdge {
  id: string
  source_id: string
  sourceId?: string
  target_id: string
  targetId?: string
  edge_type: GraphEdgeType
  edgeType?: GraphEdgeType
  label: string
  fieldname?: string | null
  confidence: number
  metadata: Record<string, unknown>
}

export interface GraphNeighborhood {
  root: GraphNode
  nodes: GraphNode[]
  edges: GraphEdge[]
  depth: number
  truncated: boolean
}

export interface RelatedDocumentsResponse {
  doctype: string
  name: string
  related: GraphNeighborhood
}

export interface TimelineEvent {
  id: string
  doctype: string
  name: string
  label: string
  event_type: string
  eventType?: string
  event_date?: string | null
  eventDate?: string | null
  status?: string | null
  metadata: Record<string, unknown>
}

export interface BusinessTimeline {
  root: GraphNode
  events: TimelineEvent[]
}

export interface ReasoningRequest {
  question: string
  doctype?: string | null
  name?: string | null
  depth?: number
}

export interface ReasoningResponse {
  answer: string
  related?: GraphNeighborhood | null
  confidence: number
}
