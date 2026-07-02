import { useState } from 'react'
import { AlertTriangle, CheckCircle2, Loader2, XCircle } from 'lucide-react'
import { useCancelCrud, useConfirmCrud } from '../../hooks/api/useChat'
import type { ConfirmationPart } from '../../types/chat'

export function ConfirmationCard({part}:{part:ConfirmationPart}) {
  const confirm=useConfirmCrud()
  const cancel=useCancelCrud()
  const [state,setState]=useState<'pending'|'confirmed'|'cancelled'>('pending')
  const [message,setMessage]=useState<string>()
  const busy=confirm.isPending||cancel.isPending

  const onConfirm=()=>confirm.mutate(part.confirmation_id,{onSuccess:result=>{setState('confirmed');setMessage(result.message)}})
  const onCancel=()=>cancel.mutate(part.confirmation_id,{onSuccess:()=>{setState('cancelled');setMessage('Action cancelled. No ERPNext record was changed.')}})

  if(state!=='pending') return <div className={`rounded-xl border p-4 ${state==='confirmed'?'border-emerald-200 bg-emerald-50':'border-slate-200 bg-slate-50'}`}><div className="flex items-start gap-2.5">{state==='confirmed'?<CheckCircle2 size={18} className="mt-0.5 text-emerald-600"/>:<XCircle size={18} className="mt-0.5 text-slate-500"/>}<div><p className="text-sm font-bold text-slate-800">{state==='confirmed'?'Action completed':'Action cancelled'}</p><p className="mt-1 text-xs text-slate-600">{message}</p></div></div></div>

  const error=confirm.error||cancel.error
  return <div className="rounded-xl border border-amber-200 bg-amber-50 p-4"><div className="flex gap-3"><AlertTriangle size={19} className="mt-0.5 shrink-0 text-amber-600"/><div className="min-w-0 flex-1"><div className="flex flex-wrap items-center gap-2"><p className="text-sm font-bold text-amber-950">{part.title}</p><span className="rounded-full bg-amber-200/70 px-2 py-0.5 text-[9px] font-extrabold uppercase tracking-wider text-amber-800">{part.risk_level} risk</span></div><p className="mt-1 text-xs leading-5 text-amber-800">{part.description}</p><div className="mt-3 flex flex-wrap gap-2"><button type="button" disabled={busy} onClick={onConfirm} className="inline-flex items-center gap-1.5 rounded-lg bg-amber-600 px-3 py-2 text-xs font-bold text-white hover:bg-amber-700 disabled:opacity-50">{confirm.isPending&&<Loader2 size={13} className="animate-spin"/>}{part.confirm_label}</button><button type="button" disabled={busy} onClick={onCancel} className="rounded-lg bg-white px-3 py-2 text-xs font-bold text-amber-900 ring-1 ring-amber-200 hover:bg-amber-100 disabled:opacity-50">{part.cancel_label}</button></div>{error&&<p className="mt-2 text-xs font-semibold text-rose-700">{error instanceof Error?error.message:'The action could not be completed.'}</p>}<p className="mt-3 text-[10px] font-medium text-amber-700">Nothing is written until you confirm. Permission is checked again at execution time.</p></div></div></div>
}
