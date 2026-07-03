import {Paperclip} from 'lucide-react'
import type {MailAttachment} from '../types/communication.types'
export function MailAttachmentPanel({items}:{items:MailAttachment[]}){if(!items.length)return null;return <div className="mt-4"><p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Attachments</p><div className="mt-2 flex flex-wrap gap-2">{items.map(file=><span key={file.name} className="inline-flex items-center gap-1.5 rounded-lg border bg-slate-50 px-2.5 py-2 text-xs text-slate-600"><Paperclip size={12}/>{file.file_name}</span>)}</div></div>}
