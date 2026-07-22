export type EntitySearchContext = {
  parent_doctype?: string | null
  company?: string | null
  supplier?: string | null
  customer?: string | null
  warehouse?: string | null
}

export type EntitySearchRequest = {
  doctype: string
  query: string
  search_fields?: string[]
  context?: EntitySearchContext
  limit?: number
}

export type EntityMatch = {
  value: string
  label: string
  description?: string | null
  match_type: string
  score: number
  disabled: boolean
  metadata: Record<string, unknown>
}

export type EntitySearchResponse = {
  doctype: string
  query: string
  matches: EntityMatch[]
  has_more: boolean
}
