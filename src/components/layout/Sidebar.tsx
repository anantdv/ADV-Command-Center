import { useEffect, useState, type ComponentType } from 'react'
import { NavLink, useLocation } from 'react-router-dom'
import {
  Boxes, ChevronDown, ChevronLeft, ChevronRight,
  GraduationCap, Headphones, LayoutDashboard, Library, Menu, Settings, ShieldCheck,
  Sparkles, X, type LucideProps,
} from 'lucide-react'
import { cn } from '../../utils/cn'
import { useAppStore } from '../../store/useAppStore'
import { BrandLogo } from '../common/BrandLogo'

type Child = { label: string; path: string }
type Item = { label: string; path: string; icon: ComponentType<LucideProps>; children?: Child[] }
const nav: Item[] = [
  { label: 'Overview', path: '/overview', icon: LayoutDashboard },
  { label: 'Command Center', path: '/command-center', icon: Sparkles },
  { label: 'Modules', path: '/modules', icon: Boxes, children: ['Accounting','Selling','Buying','Stock','CRM','Projects','HR','Manufacturing'].map(x => ({ label: x, path: `/modules/${x.toLowerCase()}` })) },
  { label: 'Library', path: '/library', icon: Library, children: [{label:'Spreadsheets',path:'/library/spreadsheets'},{label:'PDF Reports',path:'/library/pdf'},{label:'Charts',path:'/library/charts'},{label:'Dashboards',path:'/library/dashboards'}] },
  { label: 'Training', path: '/training', icon: GraduationCap, children: [{label:'Courses',path:'/training/courses'},{label:'Assessments',path:'/training/assessments'},{label:'Leaderboard',path:'/training/leaderboard'}] },
  { label: 'Support', path: '/support', icon: Headphones, children: [{label:'AI Help',path:'/support/ai-help'},{label:'Tickets',path:'/support/tickets'}] },
  { label: 'Settings', path: '/settings', icon: Settings },
]

export function Sidebar() {
  const { sidebarCollapsed: collapsed, toggleSidebar, mobileOpen, setMobileOpen } = useAppStore()
  const { pathname } = useLocation()
  const [open, setOpen] = useState<Record<string, boolean>>({})
  useEffect(() => { setMobileOpen(false); const parent = nav.find(n => n.children?.some(c => pathname.startsWith(c.path))); if (parent) setOpen(s => ({ ...s, [parent.label]: true })) }, [pathname, setMobileOpen])
  return <>
    {mobileOpen && <button aria-label="Close sidebar" onClick={() => setMobileOpen(false)} className="fixed inset-0 z-40 bg-slate-950/50 backdrop-blur-sm lg:hidden" />}
    <aside className={cn('fixed inset-y-0 left-0 z-50 flex flex-col overflow-hidden bg-[radial-gradient(circle_at_20%_0%,#242a5f_0,#11162a_34%,#090d19_100%)] text-white transition-all duration-300 lg:sticky lg:top-0 lg:h-screen', collapsed ? 'lg:w-[80px]' : 'lg:w-[248px]', mobileOpen ? 'w-[280px] translate-x-0' : 'w-[280px] -translate-x-full lg:translate-x-0')}>
      <div className="flex h-[72px] items-center gap-3 border-b border-white/[.07] px-5">
        <BrandLogo className="size-10"/>
        {!collapsed && <div className="min-w-0"><p className="truncate font-[Manrope] text-sm font-bold">ADV</p><p className="truncate text-[10px] text-slate-400">Command Center</p></div>}
        <button onClick={() => setMobileOpen(false)} className="ml-auto rounded-lg p-2 text-slate-400 lg:hidden"><X size={18} /></button>
      </div>
      <nav className="flex-1 overflow-y-auto px-3 py-5 scrollbar-thin">
        {!collapsed && <p className="mb-3 px-3 text-[9px] font-bold uppercase tracking-[.18em] text-slate-500">Workspace</p>}
        <div className="space-y-1">
          {nav.map(item => {
            const active = pathname === item.path || (item.children && pathname.startsWith(item.path + '/'))
            const Icon = item.icon
            return <div key={item.label}>
              <div className={cn('group flex items-center rounded-xl transition', active ? 'bg-gradient-to-r from-indigo-500/25 to-violet-500/10 text-white ring-1 ring-inset ring-white/[.06]' : 'text-slate-400 hover:bg-white/[.05] hover:text-white')}>
                <NavLink to={item.path} title={collapsed ? item.label : undefined} className="flex min-w-0 flex-1 items-center gap-3 px-3 py-2.5">
                  <Icon size={18} className={cn('shrink-0', active && 'text-indigo-300')} />{!collapsed && <span className="truncate text-[13px] font-semibold">{item.label}</span>}
                </NavLink>
                {!collapsed && item.children && <button aria-label={`Toggle ${item.label}`} onClick={() => setOpen(s => ({...s,[item.label]:!s[item.label]}))} className="mr-2 rounded p-1 text-slate-500"><ChevronDown size={14} className={cn('transition', open[item.label] && 'rotate-180')} /></button>}
              </div>
              {!collapsed && item.children && open[item.label] && <div className="ml-6 mt-1 space-y-0.5 border-l border-white/10 pl-4">{item.children.map(child => <NavLink key={child.path} to={child.path} className={({isActive}) => cn('block rounded-lg px-3 py-2 text-xs font-medium transition', isActive ? 'bg-white/[.06] text-indigo-300' : 'text-slate-500 hover:text-slate-200')}>{child.label}</NavLink>)}</div>}
            </div>
          })}
        </div>
      </nav>
      <div className="border-t border-white/[.07] p-3">
        {!collapsed && <div className="mb-3 rounded-xl border border-white/[.07] bg-white/[.035] p-3"><div className="flex items-center gap-2 text-[11px] font-semibold text-slate-300"><ShieldCheck size={14} className="text-emerald-400" />System Manager</div><p className="mt-1.5 text-[10px] leading-4 text-slate-500">All ERP permissions synced</p></div>}
        <button onClick={toggleSidebar} className="hidden w-full items-center justify-center gap-2 rounded-xl py-2 text-xs text-slate-500 transition hover:bg-white/[.05] hover:text-white lg:flex">{collapsed ? <ChevronRight size={18} /> : <><ChevronLeft size={16} /> Collapse sidebar</>}</button>
      </div>
    </aside>
  </>
}

export function MobileMenuButton() { const setMobileOpen = useAppStore(s => s.setMobileOpen); return <button aria-label="Open menu" onClick={() => setMobileOpen(true)} className="rounded-xl border border-slate-200 bg-white p-2.5 text-slate-600 lg:hidden"><Menu size={19} /></button> }
