import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Bell, ChevronDown, LogOut, ShieldCheck } from 'lucide-react'
import { MobileMenuButton } from './Sidebar'
import { useAuthStore } from '../../store/useAuthStore'
import { NotificationTicker } from './NotificationTicker'
import { GlobalDateRangePicker } from './GlobalDateRangePicker'

export function TopHeader() {
  const [userOpen,setUserOpen]=useState(false);const {user,logout}=useAuthStore();const navigate=useNavigate()
  const displayName=user?.fullName||user?.user||'ERP User';const initials=displayName.split(/\s+/).map(part=>part[0]).join('').slice(0,2).toUpperCase();const company=user?.company||'ERPNext';const companyInitials=company.split(/\s+/).map(part=>part[0]).join('').slice(0,3).toUpperCase();const signOut=async()=>{await logout();navigate('/login',{replace:true})}
  return <header className="sticky top-0 z-30 flex h-[72px] items-center gap-3 border-b border-slate-200/80 bg-white/90 px-4 backdrop-blur-xl sm:px-6 lg:px-8"><MobileMenuButton/><NotificationTicker/><div className="ml-auto flex items-center gap-1.5 sm:gap-2">
    <div title={company} className="hidden max-w-56 items-center gap-2 rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs font-semibold text-slate-700 xl:flex"><span className="flex size-5 shrink-0 items-center justify-center rounded-md bg-indigo-50 text-[9px] font-bold text-indigo-600">{companyInitials}</span><span className="truncate">{company}</span></div>
    <GlobalDateRangePicker/>
    <button aria-label="Notifications" className="relative rounded-xl p-2.5 text-slate-500 transition hover:bg-slate-100"><Bell size={19}/><span className="absolute right-2 top-2 size-2 rounded-full border-2 border-white bg-rose-500"/></button><div className="mx-1 hidden h-7 w-px bg-slate-200 sm:block"/><div className="relative"><button onClick={()=>setUserOpen(open=>!open)} aria-expanded={userOpen} className="flex items-center gap-2 rounded-xl p-1.5 text-left transition hover:bg-slate-50"><div className="flex size-8 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-violet-600 text-xs font-bold text-white">{initials}</div><div className="hidden sm:block"><p className="max-w-32 truncate text-xs font-bold text-slate-800">{displayName}</p><p className="text-[10px] text-slate-400">ERPNext User</p></div><ChevronDown size={13} className={`hidden text-slate-400 transition sm:block ${userOpen?'rotate-180':''}`}/></button>{userOpen&&<div className="absolute right-0 top-12 w-56 rounded-2xl border bg-white p-2 shadow-xl"><div className="border-b px-3 py-2.5"><p className="truncate text-xs font-bold text-slate-800">{displayName}</p><p className="mt-1 flex items-center gap-1 text-[10px] text-emerald-600"><ShieldCheck size={11}/>ERPNext session active</p></div><button onClick={signOut} className="mt-1 flex w-full items-center gap-2 rounded-xl px-3 py-2.5 text-left text-xs font-bold text-rose-600 hover:bg-rose-50"><LogOut size={15}/>Sign out</button></div>}</div>
  </div></header>
}
