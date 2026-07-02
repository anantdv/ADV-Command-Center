import type { ReactNode } from 'react'
import { MoreHorizontal } from 'lucide-react'

export function ChartCard({ title, subtitle, children, className = '' }: { title: string; subtitle?: string; children: ReactNode; className?: string }) {
  return <section className={`card min-w-0 p-5 ${className}`}>
    <div className="mb-5 flex items-start justify-between">
      <div><h3 className="font-[Manrope] text-sm font-bold text-slate-900">{title}</h3>{subtitle && <p className="mt-1 text-xs text-slate-400">{subtitle}</p>}</div>
      <button aria-label="Chart options" className="rounded-lg p-1.5 text-slate-400 transition hover:bg-slate-100 hover:text-slate-700"><MoreHorizontal size={18} /></button>
    </div>
    {children}
  </section>
}
