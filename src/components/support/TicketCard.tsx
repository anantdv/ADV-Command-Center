import type { Ticket } from '../../types'
import { StatusBadge } from '../common/Badges'
export function TicketCard({ticket}:{ticket:Ticket}){return <article className="card p-4"><div className="flex items-center justify-between"><span className="text-xs font-bold text-indigo-600">{ticket.id}</span><StatusBadge>{ticket.status}</StatusBadge></div><h3 className="mt-3 text-sm font-bold">{ticket.subject}</h3><div className="mt-4 flex items-center justify-between border-t pt-3 text-[10px] text-slate-400"><span>{ticket.assignedTo}</span><StatusBadge>{ticket.priority}</StatusBadge></div></article>}
