import {apiClient} from '../../../services/apiClient'
import type {ActionResult,AiDraft,CommunicationList,CommunicationThread,ComposerData,EmailTemplate,MailFolder} from '../types/communication.types'

const query=(values:Record<string,unknown>)=>new URLSearchParams(Object.entries(values).filter(([,v])=>v!==undefined&&v!==''&&v!==false).map(([k,v])=>[k,String(v)])).toString()
export const communicationApi={
  list:(options:{folder:MailFolder;search?:string;unread?:boolean;linked?:boolean;has_attachments?:boolean;reference_doctype?:string})=>apiClient.get<CommunicationList>(`/api/communications?${query(options)}`),
  thread:(name:string)=>apiClient.get<CommunicationThread>(`/api/communications/${encodeURIComponent(name)}`),
  templates:()=>apiClient.get<EmailTemplate[]>('/api/communications/templates'),
  renderTemplate:(name:string)=>apiClient.post<EmailTemplate>(`/api/communications/templates/${encodeURIComponent(name)}/render`,{context:{}}),
  send:(data:ComposerData)=>apiClient.post<ActionResult>('/api/communications/send',data),
  reply:(name:string,data:{content:string;cc:string[];bcc:string[];attachments:string[]})=>apiClient.post<ActionResult>(`/api/communications/${encodeURIComponent(name)}/reply`,data),
  forward:(name:string,data:{to:string[];content:string;cc:string[];bcc:string[];attachments:string[]})=>apiClient.post<ActionResult>(`/api/communications/${encodeURIComponent(name)}/forward`,data),
  link:(name:string,reference_doctype:string,reference_name:string)=>apiClient.post<ActionResult>(`/api/communications/${encodeURIComponent(name)}/link`,{reference_doctype,reference_name}),
  aiDraft:(communication_name:string,instruction:string,content?:string)=>apiClient.post<AiDraft>('/api/communications/ai/draft',{communication_name,instruction,content}),
  convert:(name:string,action:'task'|'issue'|'lead')=>apiClient.post<ActionResult>(`/api/communications/${encodeURIComponent(name)}/convert`,{action}),
}
