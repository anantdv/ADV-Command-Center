import { AlertTriangle, BellRing, CheckCircle2, ClipboardCheck, FileWarning, PackageSearch, Ticket, Timer } from 'lucide-react'
import { Link } from 'react-router-dom'
import { useNotificationTicker } from '../../hooks/api/useNotifications'
import type { NotificationTickerItem } from '../../types/notifications'

const typeTone: Record<NotificationTickerItem['type'], string> = {
  approval: 'bg-purple-500',
  invoice: 'bg-amber-500',
  issue: 'bg-rose-500',
  task: 'bg-emerald-500',
  stock: 'bg-teal-500',
  system: 'bg-slate-500',
  event: 'bg-cyan-500',
}
const priorityIcon = { low: CheckCircle2, medium: BellRing, high: AlertTriangle, critical: AlertTriangle }
const typeIcon = { approval: ClipboardCheck, invoice: FileWarning, issue: Ticket, task: Timer, stock: PackageSearch, system: BellRing, event: BellRing }

export function NotificationTicker() {
  const query = useNotificationTicker()
  const items = query.data || []
  if (query.isLoading) return <div className="hidden h-10 flex-1 items-center rounded-xl bg-slate-50 px-4 text-xs font-semibold text-slate-400 md:flex">Loading business events…</div>
  if (!items.length) return <div className="hidden h-10 flex-1 items-center rounded-xl bg-slate-50 px-4 text-xs font-semibold text-slate-400 md:flex">No urgent notifications</div>
  return <div className="group hidden h-10 flex-1 overflow-hidden rounded-xl border border-slate-200 bg-slate-50/80 md:block">
    <div className="flex h-full w-max animate-[ticker_36s_linear_infinite] items-center gap-3 px-3 group-hover:[animation-play-state:paused]">
      {[...items, ...items].map((item, index) => <TickerItem key={`${item.id}-${index}`} item={item}/>)}
    </div>
  </div>
}

function TickerItem({ item }: { item: NotificationTickerItem }) {
  const Icon = typeIcon[item.type] || priorityIcon[item.priority]
  const content = <span className="inline-flex items-center gap-2 whitespace-nowrap rounded-full bg-white px-3 py-1.5 text-[11px] font-semibold text-slate-600 shadow-sm">
    <span className={`size-2 rounded-full ${typeTone[item.type]}`}/>
    <Icon size={13} className={item.priority==='critical'?'text-rose-600':'text-slate-400'}/>
    <span className="font-bold text-slate-800">{item.label}</span>
    <span>{item.message}</span>
  </span>
  return item.route ? <Link to={item.route}>{content}</Link> : content
}
