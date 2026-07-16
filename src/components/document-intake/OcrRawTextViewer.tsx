import { useState } from 'react'

export function OcrRawTextViewer({text}:{text?:string|null}){
  const [open,setOpen]=useState(false)
  const [copied,setCopied]=useState(false)
  if(!text)return null
  return <div className="mt-4 rounded-xl border border-slate-200">
    <div className="flex items-center justify-between px-3 py-2"><button type="button" onClick={()=>setOpen(value=>!value)} className="text-xs font-bold text-slate-600">View extracted text <span>{open?'−':'+'}</span></button>{open&&<button type="button" onClick={()=>{void navigator.clipboard?.writeText(text);setCopied(true);setTimeout(()=>setCopied(false),1200)}} className="text-[10px] font-bold text-indigo-600">{copied?'Copied':'Copy Text'}</button>}</div>
    {open&&<pre className="max-h-72 overflow-auto whitespace-pre-wrap border-t bg-slate-950 p-4 font-mono text-[12px] leading-6 text-slate-100">{text}</pre>}
  </div>
}
