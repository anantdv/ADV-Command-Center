import { create } from 'zustand'
import type { AppDateRange } from '../types/dateRange'

type AppState = {
  sidebarCollapsed: boolean
  mobileOpen: boolean
  toggleSidebar: () => void
  setMobileOpen: (open: boolean) => void
  dateRange: AppDateRange
  setDateRange: (range: AppDateRange) => void
}

const iso=(date:Date)=>`${date.getFullYear()}-${String(date.getMonth()+1).padStart(2,'0')}-${String(date.getDate()).padStart(2,'0')}`
const today=new Date()
const defaultRange: AppDateRange={from:iso(new Date(today.getFullYear(),today.getMonth(),1)),to:iso(today),label:'This Month',preset:'this_month'}
const stored=typeof localStorage!=='undefined'?localStorage.getItem('adv_date_range'):null
const initialRange: AppDateRange=stored?{...defaultRange,...JSON.parse(stored)}:defaultRange

export const useAppStore = create<AppState>((set) => ({
  sidebarCollapsed: false,
  mobileOpen: false,
  toggleSidebar: () => set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed })),
  setMobileOpen: (mobileOpen) => set({ mobileOpen }),
  dateRange: initialRange,
  setDateRange: (dateRange) => { localStorage.setItem('adv_date_range', JSON.stringify(dateRange)); set({dateRange}) },
}))
