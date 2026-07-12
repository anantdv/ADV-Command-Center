export type DateRangePreset = 'today' | 'this_week' | 'this_month' | 'this_quarter' | 'this_year' | 'last_month' | 'last_quarter' | 'last_year' | 'custom'

export interface GlobalDateRange {
  preset: DateRangePreset
  fromDate: string
  toDate: string
}

export type AppDateRange = {
  from: string
  to: string
  label: string
  preset?: DateRangePreset
}
