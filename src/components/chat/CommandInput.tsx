import { Paperclip, Send, Mic, Sparkles } from 'lucide-react'
import { useEffect, useState, type FormEvent } from 'react'

export function CommandInput({ onSend, compact = false, initialValue = '' }: { onSend?: (text: string) => void; compact?: boolean; initialValue?: string }) {
  const [text, setText] = useState('')
  useEffect(()=>{setText(initialValue)},[initialValue])
  const submit = (e: FormEvent) => { e.preventDefault(); if (!text.trim()) return; onSend?.(text); setText('') }
  return <form onSubmit={submit} className="rounded-2xl border border-slate-200 bg-white p-2 shadow-[0_10px_40px_rgba(15,23,42,.10)] transition focus-within:border-indigo-300 focus-within:ring-4 focus-within:ring-indigo-50">
    {!compact && <textarea value={text} onChange={e => setText(e.target.value)} onKeyDown={e => { if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();submit(e)} }} rows={2} placeholder="Ask Tinni anything about your business…" className="max-h-32 min-h-[52px] w-full resize-none bg-transparent px-3 py-2 text-sm outline-none placeholder:text-slate-400" />}
    {compact && <input value={text} onChange={e => setText(e.target.value)} placeholder="Ask AI about this module…" className="h-10 w-full bg-transparent px-3 text-sm outline-none placeholder:text-slate-400" />}
    <div className="flex items-center justify-between px-1 pb-0.5">
      <div className="flex items-center gap-1"><button type="button" aria-label="Attach file" className="rounded-lg p-2 text-slate-400 transition hover:bg-slate-100 hover:text-slate-700"><Paperclip size={17} /></button><button type="button" aria-label="Voice input" className="rounded-lg p-2 text-slate-400 transition hover:bg-slate-100 hover:text-slate-700"><Mic size={17} /></button><span className="ml-1 hidden items-center gap-1 text-[10px] font-semibold text-slate-400 sm:flex"><Sparkles size={11} />ERP context enabled</span></div>
      <button type="submit" aria-label="Send command" className="flex size-9 items-center justify-center rounded-xl bg-indigo-600 text-white transition hover:bg-indigo-700 disabled:opacity-40" disabled={!text.trim()}><Send size={16} /></button>
    </div>
  </form>
}
