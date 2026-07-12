import type { ReactNode } from 'react'
import { X } from 'lucide-react'

export function ResultActionDialog({open,title,description,children,onClose}:{open:boolean;title:string;description?:string;children:ReactNode;onClose:()=>void}){
  if(!open)return null
  return <div className="fixed inset-0 z-50 grid place-items-center bg-slate-950/35 p-4">
    <div className="w-full max-w-lg rounded-2xl border border-slate-200 bg-white p-5 shadow-2xl">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-sm font-bold text-slate-900">{title}</h2>
          {description&&<p className="mt-1 text-xs leading-5 text-slate-500">{description}</p>}
        </div>
        <button type="button" onClick={onClose} className="rounded-lg p-2 text-slate-400 hover:bg-slate-100 hover:text-slate-700"><X size={16}/></button>
      </div>
      <div className="mt-5">{children}</div>
    </div>
  </div>
}
