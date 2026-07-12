import { CheckCircle2, LockKeyhole } from 'lucide-react'
import type { ReactNode } from 'react'

const statusTone: Record<string, string> = {
  Open: 'bg-blue-50 text-blue-700', 'In Progress': 'bg-amber-50 text-amber-700', Resolved: 'bg-emerald-50 text-emerald-700',
  High: 'bg-rose-50 text-rose-700', Medium: 'bg-amber-50 text-amber-700', Low: 'bg-slate-100 text-slate-600',
}
export function StatusBadge({ children }: { children: ReactNode }) { return <span className={`inline-flex rounded-full px-2.5 py-1 text-[11px] font-bold ${statusTone[String(children)] || 'bg-slate-100 text-slate-600'}`}>{children}</span> }
export function PermissionBadge({ label = '', allowed = true, reason }: { label?: string; allowed?: boolean; reason?: string }) { if(allowed&&!label)return null;return <span title={reason} className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[10px] font-bold ${allowed?'border-indigo-100 bg-indigo-50 text-indigo-700':'border-amber-100 bg-amber-50 text-amber-700'}`}>{allowed?<CheckCircle2 size={11}/>:<LockKeyhole size={11}/>} {allowed?label:'Access Restricted'}</span> }
export function PrivacyBadge({ label }: { label: string }) { return <span className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500"><LockKeyhole size={12} />{label}</span> }
