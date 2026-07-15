import { Paperclip, Send, Mic, Sparkles, Loader2 } from 'lucide-react'
import { useEffect, useRef, useState, type FormEvent } from 'react'
import { useDocumentUpload, useProcessDocument } from '../../hooks/api/useDocumentIntake'
import { useVoiceInput } from '../../hooks/useVoiceInput'
import type { DocumentMappingPreview } from '../../types/documentIntake'

const MAX_CLIENT_UPLOAD_MB = 20
const ACCEPTED_TYPES = '.pdf,.png,.jpg,.jpeg,.webp,.docx'

export function CommandInput({ onSend, compact = false, initialValue = '', onOcrProcessed, onAttachmentMessage, onAttachmentError }: { onSend?: (text: string) => void; compact?: boolean; initialValue?: string; onOcrProcessed?: (preview: DocumentMappingPreview) => void; onAttachmentMessage?: (text: string) => void; onAttachmentError?: (message: string) => void }) {
  const [text, setText] = useState('')
  const [status, setStatus] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const upload = useDocumentUpload()
  const process = useProcessDocument()
  const voice = useVoiceInput({
    onTranscript: transcript => setText(value => transcript || value),
    onError: error => setStatus(error),
  })
  useEffect(()=>{setText(initialValue)},[initialValue])
  const submit = (e: FormEvent) => { e.preventDefault(); if (!text.trim()) return; onSend?.(text); setText(''); setStatus(null) }
  const busy = upload.isPending || process.isPending
  const handleFileSelected = async (file?: File) => {
    if (!file) return
    const sizeMb = file.size / (1024 * 1024)
    if (sizeMb > MAX_CLIENT_UPLOAD_MB) {
      setStatus(`File is too large. Please upload files below ${MAX_CLIENT_UPLOAD_MB} MB.`)
      return
    }
    try {
      setStatus(`Uploading ${file.name}…`)
      onAttachmentMessage?.(`Uploaded ${file.name}`)
      const uploaded = await upload.mutateAsync(file)
      setStatus('Processing OCR intake…')
      const preview = await process.mutateAsync(uploaded.intake_id)
      setStatus('I extracted the document. Please review the draft mapping.')
      onOcrProcessed?.(preview)
    } catch (error) {
      const message=error instanceof Error ? error.message : 'OCR intake failed.'
      setStatus(message)
      onAttachmentError?.(message)
    } finally {
      if (fileInputRef.current) fileInputRef.current.value = ''
    }
  }
  return <form onSubmit={submit} className="rounded-2xl border border-slate-200 bg-white p-2 shadow-[0_10px_40px_rgba(15,23,42,.10)] transition focus-within:border-indigo-300 focus-within:ring-4 focus-within:ring-indigo-50">
    {!compact && <textarea value={text} onChange={e => setText(e.target.value)} onKeyDown={e => { if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();submit(e)} }} rows={2} placeholder="Ask Tinni anything about your business…" className="max-h-32 min-h-[52px] w-full resize-none bg-transparent px-3 py-2 text-sm outline-none placeholder:text-slate-400" />}
    {compact && <input value={text} onChange={e => setText(e.target.value)} placeholder="Ask AI about this module…" className="h-10 w-full bg-transparent px-3 text-sm outline-none placeholder:text-slate-400" />}
    {status&&<p className={`px-3 pb-1 text-[10px] font-semibold ${status.includes('failed')||status.includes('not supported')||status.includes('large')?'text-rose-600':'text-slate-400'}`}>{voice.listening?'Listening… ':''}{status}</p>}
    <div className="flex items-center justify-between px-1 pb-0.5">
      <div className="flex items-center gap-1"><input ref={fileInputRef} type="file" accept={ACCEPTED_TYPES} hidden onChange={event=>void handleFileSelected(event.target.files?.[0])}/><button type="button" aria-label="Attach file" onClick={()=>fileInputRef.current?.click()} disabled={busy} className="rounded-lg p-2 text-slate-400 transition hover:bg-slate-100 hover:text-slate-700 disabled:opacity-40">{busy?<Loader2 size={17} className="animate-spin"/>:<Paperclip size={17} />}</button><button type="button" aria-label="Voice input" onClick={voice.toggle} disabled={busy} className={`rounded-lg p-2 transition hover:bg-slate-100 disabled:opacity-40 ${voice.listening?'animate-pulse bg-rose-50 text-rose-600':'text-slate-400 hover:text-slate-700'}`}><Mic size={17} /></button><span className="ml-1 hidden items-center gap-1 text-[10px] font-semibold text-slate-400 sm:flex"><Sparkles size={11} />ERP context enabled</span></div>
      <button type="submit" aria-label="Send command" className="flex size-9 items-center justify-center rounded-xl bg-indigo-600 text-white transition hover:bg-indigo-700 disabled:opacity-40" disabled={!text.trim()||busy}><Send size={16} /></button>
    </div>
  </form>
}
