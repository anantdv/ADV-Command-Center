import {MailOpen} from 'lucide-react'
export function MailEmptyState(){return <div className="grid h-full place-items-center p-8 text-center"><div><MailOpen className="mx-auto text-slate-300" size={36}/><p className="mt-3 text-sm font-bold text-slate-600">No communications found</p><p className="mt-1 text-xs text-slate-400">Try another folder or adjust the filters.</p></div></div>}
