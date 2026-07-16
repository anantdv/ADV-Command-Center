import { useState } from 'react'

export function OcrRawTextViewer({text}:{text?:string|null}){
  const [open,setOpen]=useState(false)
  if(!text)return null
  return <div className="mt-4 rounded-xl border border-slate-200">
    <button type="button" onClick={()=>setOpen(value=>!value)} className="flex w-full items-center justify-between px-3 py-2 text-xs font-bold text-slate-600">
      View extracted text <span>{open?'−':'+'}</span>
    </button>
    {open&&<pre className="max-h-56 overflow-auto border-t bg-slate-950 p-3 text-[11px] leading-5 text-slate-100">{text}</pre>}
  </div>
}
