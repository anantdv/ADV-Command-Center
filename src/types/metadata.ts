export type FieldImportance = 'required' | 'recommended' | 'optional' | 'hidden' | 'read_only' | 'computed'

export type FieldIntelligence = {
  fieldname: string
  label: string
  fieldtype: string
  required: boolean
  read_only: boolean
  hidden: boolean
  permlevel: number
  options?: string | null
  link_to?: string | null
  child_doctype?: string | null
  depends_on?: string | null
  fetch_from?: string | null
  default?: unknown
  description?: string | null
  aliases: string[]
  examples: string[]
  importance: FieldImportance
  writable: boolean
  searchable: boolean
  section?: string | null
}

export type ChildTableIntelligence = {
  fieldname: string
  label: string
  child_doctype: string
  required: boolean
  link_fields: FieldIntelligence[]
  editable_fields: FieldIntelligence[]
  required_fields: string[]
  field_priority: string[]
}

export type DoctypeIntelligence = {
  doctype: string
  module?: string | null
  title_field?: string | null
  is_submittable: boolean
  fields: FieldIntelligence[]
  child_tables: ChildTableIntelligence[]
  mandatory_fields: string[]
  writable_fields: string[]
  link_fields: FieldIntelligence[]
  search: {
    title_field?: string | null
    search_fields: string[]
    display_fields: string[]
  }
  workflow: {
    is_submittable: boolean
    workflow_state_field?: string | null
    states: string[]
    actions: string[]
  }
  diagnostics: Record<string, unknown>
}

export type FormLayoutIntelligence = {
  sections: Array<{ title: string; fields: string[] }>
  tabs: Array<Record<string, unknown>>
  fields: FieldIntelligence[]
  child_tables: ChildTableIntelligence[]
}

