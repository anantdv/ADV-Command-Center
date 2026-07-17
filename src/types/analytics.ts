export type AnalyticsRunRequest={
  analyticsKey?:string
  analytics_key?:string
  dateRange?:Record<string,unknown>|null
  date_range?:Record<string,unknown>|null
  filters?:Record<string,unknown>
  chartType?:string|null
  chart_type?:string|null
  limit?:number|null
  moduleContext?:string|null
}

export type AnalyticsResult={
  analyticsKey:string
  title:string
  summary:string
  columns:Array<{key:string;label:string;type?:string}>
  rows:Array<Record<string,unknown>>
  chart?:Record<string,unknown>|null
  filters?:Record<string,unknown>
  filtersApplied?:Record<string,unknown>
  source?:Record<string,unknown>
  permission?:Record<string,unknown>|null
  drilldown?:Record<string,unknown>|null
  resultId?:string|null
}

export type AnalyticsDefinition={
  key:string
  title:string
  description?:string|null
  module:string
  sourceType:'doctype'|'standard_report'|'composite'
  sourceName:string
  defaultChart:string
}
