import { create } from 'zustand'

type AppState = {
  sidebarCollapsed: boolean
  mobileOpen: boolean
  toggleSidebar: () => void
  setMobileOpen: (open: boolean) => void
  dateRange: { from: string; to: string; label: string }
  setDateRange: (range: { from: string; to: string; label: string }) => void
}

const iso=(date:Date)=>`${date.getFullYear()}-${String(date.getMonth()+1).padStart(2,'0')}-${String(date.getDate()).padStart(2,'0')}`
const today=new Date()
const initialRange={from:iso(new Date(today.getFullYear(),today.getMonth(),1)),to:iso(today),label:'This month'}

export const useAppStore = create<AppState>((set) => ({
  sidebarCollapsed: false,
  mobileOpen: false,
  toggleSidebar: () => set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed })),
  setMobileOpen: (mobileOpen) => set({ mobileOpen }),
  dateRange: initialRange,
  setDateRange: (dateRange) => set({dateRange}),
}))
