import { useEffect, useRef, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { Clock3, FileUp, LayoutDashboard, MessageSquarePlus, Pin, Search, Sparkles, X } from 'lucide-react'
import { ChatMessage as ChatBubble } from '../components/chat/ChatMessage'
import { CommandInput } from '../components/chat/CommandInput'
import { StructuredMessageParts } from '../components/chat/StructuredMessageParts'
import { ErrorState } from '../components/common/ErrorState'
import { LoadingState } from '../components/common/LoadingState'
import { TinniAvatar } from '../components/common/BrandLogo'
import { PinToDashboardButton } from '../components/chat/PinToDashboardButton'
import { SuggestedPromptButtons } from '../components/chat/SuggestedPromptButtons'
import { DocumentMappingPreview } from '../components/document-intake/DocumentMappingPreview'
import { DocumentUploadPanel } from '../components/document-intake/DocumentUploadPanel'
import { ChangeChartTypeDialog } from '../components/results/ChangeChartTypeDialog'
import { ColumnSelectorDialog } from '../components/results/ColumnSelectorDialog'
import { RefineFiltersDialog } from '../components/results/RefineFiltersDialog'
import { SaveReportViewDialog } from '../components/results/SaveReportViewDialog'
import { PinTargetDialog } from '../components/results/PinTargetDialog'
import { useConfirmDocumentDraft } from '../hooks/api/useDocumentIntake'
import { useConversationMessages, useConversations, useSendChatMessage } from '../hooks/api/useChat'
import { usePinChatResultToDashboard } from '../hooks/api/useDashboard'
import { useAppStore } from '../store/useAppStore'
import type { AssistantChatResponse, ChatMessage, SourceMeta, SuggestedAction } from '../types/chat'
import type { DashboardWidgetSource } from '../types/dashboard'
import type { SuggestedPrompt } from '../types/suggestions'
import type { DocumentMappingPreview as DocumentPreview } from '../types/documentIntake'

const prompts = [
  'Show customers',
  'Show sales invoices',
  'Show stock balance',
  'Show overdue sales invoices',
  'Show unpaid invoices.',
  'Show purchase orders.',
  'Create customer ABC Trading.',
]

export function CommandCenterPage() {
  const navigate=useNavigate()
  const [searchParams]=useSearchParams()
  const moduleContext=searchParams.get('module')||undefined
  const promptParam=searchParams.get('prompt')||''
  const autoRun=searchParams.get('autoRun')==='true'
  const conversations = useConversations()
  const sendMessage = useSendChatMessage()
  const pinSuggestion=usePinChatResultToDashboard()
  const dateRange = useAppStore(state=>state.dateRange)
  const [selectedId,setSelectedId] = useState<string>()
  const [newChat,setNewChat] = useState(false)
  const [optimisticUser,setOptimisticUser] = useState<string|null>(null)
  const [transientResponse,setTransientResponse] = useState<AssistantChatResponse|null>(null)
  const [showIntake,setShowIntake] = useState(false)
  const [intakePreview,setIntakePreview] = useState<DocumentPreview|null>(null)
  const [uiAction,setUiAction]=useState<{type:string;payload:Record<string,unknown>}|null>(null)
  const confirmIntake=useConfirmDocumentDraft()
  const endRef=useRef<HTMLDivElement>(null)
  const autoRunHandledRef=useRef(false)
  const messages=useConversationMessages(selectedId||'')

  useEffect(()=>{
    if(!selectedId&&!newChat&&conversations.data?.[0]) setSelectedId(conversations.data[0].id)
  },[conversations.data,newChat,selectedId])

  const history=messages.data||[]
  const historyHasUser=Boolean(optimisticUser&&history.some(message=>message.role==='user'&&message.content===optimisticUser))
  const historyHasResponse=Boolean(transientResponse&&history.some(message=>message.id===transientResponse.message_id))
  useEffect(()=>{endRef.current?.scrollIntoView({behavior:'smooth'})},[history.length,optimisticUser,transientResponse,sendMessage.isPending])

  const send=(text:string)=>{
    if(sendMessage.isPending)return
    setOptimisticUser(text)
    setTransientResponse(null)
    sendMessage.mutate({conversation_id:newChat?undefined:selectedId,message:text,module_context:moduleContext,date_range:{from_date:dateRange.from,to_date:dateRange.to}},{
      onSuccess:response=>{setSelectedId(response.conversation_id);setNewChat(false);setTransientResponse(response)},
    })
  }
  useEffect(()=>{
    if(autoRun&&promptParam&&!autoRunHandledRef.current){
      autoRunHandledRef.current=true
      send(promptParam)
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  },[autoRun,promptParam])
  const runAction=(action:SuggestedAction,source?:SourceMeta|null)=>{
    if(action.disabled)return
    if(action.action_type==='download_file'&&action.reason){window.location.assign(action.reason);return}
    if(action.action_type==='open_library'){navigate('/library');return}
    if(action.action_type==='open_module'){
      const moduleSlug=moduleForSource(source)
      if(moduleSlug){navigate(`/modules/${moduleSlug}`);return}
    }
    if(action.action_type==='view_related'){
      send(`show related records for ${source?.doctype||source?.source_name||'this result'}`)
      return
    }
    if(action.action_type==='refine_filters'){
      send(`refine filters for ${source?.source_name||'this result'}`)
      return
    }
    const format:Record<string,string>={generate_pdf:'pdf',export_excel:'excel',export_csv:'csv'}
    if(format[action.action_type]){
      const overdue=source?.filters&&source.filters.status==='Overdue'?'overdue ':''
      send(`generate ${format[action.action_type]} for ${overdue}${source?.source_name||'this result'}`)
    }
  }
  const runSuggestion=(suggestion:SuggestedPrompt,source?:SourceMeta|null)=>{
    if(suggestion.disabled)return
    const actionType=suggestion.actionType||suggestion.action_type||suggestion.type
    const payload=suggestion.payload||{}
    if(suggestion.type==='ui_action'){
      openUiAction(actionType,payload)
      return
    }
    if(suggestion.type==='action'&&actionType==='convert_chart_type'){
      openUiAction('open_chart_type_dialog',payload)
      return
    }
    if(suggestion.type==='prompt'&&suggestion.prompt){send(suggestion.prompt);return}
    if(suggestion.type==='export'){
      const format=String(payload.format||'xlsx')
      send(`export this result to ${format}`)
      return
    }
    if(suggestion.type==='pin'){
      const conversationId=String(payload.conversation_id||payload.conversationId||'')
      const messageId=String(payload.message_id||payload.messageId||'')
      if(conversationId&&messageId&&source){
        const dashboardSource:DashboardWidgetSource={source_type:source.source_type==='tool'?'chat_result':source.source_type,source_name:source.source_name,doctype:source.doctype||(source.source_type==='doctype'?source.source_name:null),report_name:source.report_name||(source.source_type==='report'?source.source_name:null),filters:source.filters,fields:source.fields}
        pinSuggestion.mutate({conversation_id:conversationId,message_id:messageId,title:source.source_name,widget_type:'table',source:dashboardSource,target_type:'overview'})
      }
      else openUiAction('open_pin_target_dialog',payload)
      return
    }
    if(suggestion.type==='navigation'){
      const route=payload.route
      if(typeof route==='string'){navigate(route);return}
      if(actionType==='open_library'){navigate('/library');return}
      const downloadUrl=payload.download_url||payload.downloadUrl
      if(typeof downloadUrl==='string'){window.location.assign(downloadUrl);return}
    }
    if(suggestion.type==='workflow_action'){
      const action=String(payload.action||suggestion.label)
      const doctype=String(payload.doctype||source?.doctype||source?.source_name||'document')
      const name=String(payload.name||payload.recordName||'')
      send(`${action} ${doctype} ${name}`.trim())
      return
    }
    if(suggestion.type==='crud_confirmation'){
      // Confirmation cards remain the canonical UX. This prompt keeps the action in the safe chat path.
      send(`${suggestion.label} for the current draft`)
      return
    }
    if(suggestion.prompt)send(suggestion.prompt)
  }
  const openUiAction=(actionType:string,payload:Record<string,unknown>)=>{
    const dialogMap:Record<string,string>={
      open_chart_type_dialog:'chart',
      open_column_selector_dialog:'columns',
      open_refine_filters_dialog:'filters',
      open_save_report_view_dialog:'save',
      open_pin_target_dialog:'pin',
    }
    setUiAction({type:dialogMap[actionType]||'unavailable',payload})
  }
  const runRowClick=(row:Record<string,unknown>)=>{
    const meta=row._meta as {doctype?:string;name?:string;clickable?:boolean}|undefined
    if(!meta?.clickable||!meta.doctype||!meta.name)return
    send(`show detail for ${meta.doctype} ${meta.name}`)
  }
  const startNew=()=>{setNewChat(true);setSelectedId(undefined);setOptimisticUser(null);setTransientResponse(null);sendMessage.reset()}
  const selectConversation=(id:string)=>{setSelectedId(id);setNewChat(false);setOptimisticUser(null);setTransientResponse(null);sendMessage.reset()}
  const selected=conversations.data?.find(item=>item.id===selectedId)
  const showConversation=Boolean((selectedId||newChat)&&(history.length||optimisticUser||transientResponse||sendMessage.isPending||sendMessage.isError))

  if(conversations.isLoading)return <LoadingState cards={4}/>
  if(conversations.isError)return <ErrorState retry={()=>void conversations.refetch()}/>

  return <div className="-m-4 flex h-[calc(100vh-72px)] overflow-hidden sm:-m-6 lg:-m-8">
    <aside className="hidden w-[264px] shrink-0 border-r border-slate-200 bg-white lg:flex lg:flex-col">
      <div className="p-4"><button onClick={startNew} className="btn-primary w-full"><MessageSquarePlus size={16}/>New command</button><div className="relative mt-3"><Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"/><input placeholder="Search conversations" className="h-9 w-full rounded-lg border bg-slate-50 pl-9 pr-3 text-xs outline-none focus:border-indigo-300"/></div></div>
      <div className="flex-1 overflow-y-auto px-2"><p className="eyebrow px-3 py-2">Recent</p>{conversations.data?.map(conversation=><button key={conversation.id} onClick={()=>selectConversation(conversation.id)} className={`mb-1 w-full rounded-xl p-3 text-left transition ${conversation.id===selectedId&&!newChat?'bg-indigo-50':'hover:bg-slate-50'}`}><p className={`truncate text-xs font-semibold ${conversation.id===selectedId&&!newChat?'text-indigo-700':'text-slate-700'}`}>{conversation.title}</p><p className="mt-1 flex items-center gap-1 text-[10px] text-slate-400"><Clock3 size={10}/>{new Date(conversation.updatedAt).toLocaleTimeString('en-IN',{hour:'2-digit',minute:'2-digit'})}</p></button>)}</div>
      <div className="border-t p-4"><div className="rounded-xl bg-slate-50 p-3"><p className="text-[10px] font-bold text-slate-500">CONTROLLED ACTIONS</p><p className="mt-2 text-[10px] leading-4 text-slate-400">Reads are live. Safe draft creates and field updates require your confirmation.</p></div></div>
    </aside>
    <section className="relative flex min-w-0 flex-1 flex-col bg-[#f8f9fc]">
      <div className="flex h-14 items-center justify-between border-b border-slate-200 bg-white px-4 sm:px-6"><div className="flex items-center gap-2.5"><TinniAvatar className="size-8"/><div><p className="text-sm font-bold text-slate-800">{newChat?'New command':selected?.title||'Tinni'}</p><p className="text-[10px] text-slate-400">Tinni · Live ERPNext · Controlled draft actions {moduleContext?`· ${moduleContext} context enabled`:''}</p></div></div><div className="flex items-center gap-2">{moduleContext&&<span className="rounded-full bg-indigo-50 px-2.5 py-1 text-[10px] font-bold text-indigo-700">{moduleContext} context</span>}<button onClick={()=>setShowIntake(true)} className="btn-secondary h-9 px-3 text-xs"><FileUp size={14}/>OCR intake</button><button aria-label="Pin conversation" className="hidden rounded-lg border p-2 text-slate-400 hover:bg-slate-50 sm:block"><Pin size={15}/></button></div></div>
      <div className="flex-1 overflow-y-auto scrollbar-thin">
        {!showConversation?<EmptyCommandCenter onPrompt={send}/>:<div className="mx-auto max-w-4xl space-y-7 px-4 pb-40 pt-7 sm:px-8">
          {messages.isLoading&&<LoadingState cards={2}/>} 
          {messages.isError&&<ErrorState retry={()=>void messages.refetch()}/>} 
          {history.map(message=><HistoryMessage key={message.id} message={message} onAction={runAction} onSuggestion={runSuggestion} onRowClick={runRowClick}/>)}
          {optimisticUser&&!historyHasUser&&<ChatBubble role="user">{optimisticUser}</ChatBubble>}
          {sendMessage.isPending&&<ChatBubble role="assistant"><TypingIndicator/></ChatBubble>}
          {sendMessage.isError&&<ChatBubble role="assistant"><div className="rounded-xl border border-rose-100 bg-rose-50 p-3 text-xs font-semibold text-rose-700">{sendMessage.error instanceof Error?sendMessage.error.message:'The command could not be completed.'}</div></ChatBubble>}
          {transientResponse&&!historyHasResponse&&!sendMessage.isPending&&<AssistantResponseView response={transientResponse} onAction={runAction} onSuggestion={runSuggestion} onRowClick={runRowClick}/>} 
          <div ref={endRef}/>
        </div>}
      </div>
      <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-[#f8f9fc] via-[#f8f9fc] to-transparent px-4 pb-4 pt-10 sm:px-8"><div className="mx-auto max-w-4xl"><CommandInput onSend={send} initialValue={!autoRun?promptParam:''} onAttachmentMessage={message=>{setNewChat(true);setOptimisticUser(message)}} onOcrProcessed={preview=>{setIntakePreview(preview);setShowIntake(true)}}/><p className="mt-2 text-center text-[10px] text-slate-400">ERPNext permissions always apply · Safe writes require an explicit confirmation{moduleContext?` · ${moduleContext} context enabled`:''}</p></div></div>
    </section>
    {showIntake&&<div className="fixed inset-0 z-50 grid place-items-center bg-slate-950/40 p-4"><div className="max-h-[90vh] w-full max-w-3xl overflow-y-auto rounded-2xl bg-white p-5 shadow-2xl"><div className="mb-4 flex items-center justify-between"><div><h2 className="font-bold text-slate-900">OCR Document Intake</h2><p className="text-xs text-slate-400">Upload supplier invoices, customer POs, quotations, or delivery documents.</p></div><button className="rounded-lg p-2 hover:bg-slate-100" onClick={()=>{setShowIntake(false);setIntakePreview(null)}}><X size={18}/></button></div>{intakePreview?<DocumentMappingPreview preview={intakePreview} busy={confirmIntake.isPending} onConfirm={()=>confirmIntake.mutate(intakePreview.intake_id)} onCancel={()=>setIntakePreview(null)}/>:<DocumentUploadPanel onProcessed={setIntakePreview}/>}</div></div>}
    <ChangeChartTypeDialog open={uiAction?.type==='chart'} currentType={String(uiAction?.payload.current_chart_type||uiAction?.payload.currentChartType||uiAction?.payload.chart_type||'')} onApply={()=>setUiAction(null)} onClose={()=>setUiAction(null)}/>
    <ColumnSelectorDialog open={uiAction?.type==='columns'} columns={Array.isArray(uiAction?.payload.columns)?uiAction.payload.columns.map(String):[]} onClose={()=>setUiAction(null)}/>
    <RefineFiltersDialog open={uiAction?.type==='filters'} filters={(uiAction?.payload.filters as Record<string,unknown>)||{}} onClose={()=>setUiAction(null)}/>
    <SaveReportViewDialog open={uiAction?.type==='save'} onClose={()=>setUiAction(null)}/>
    <PinTargetDialog open={uiAction?.type==='pin'} onClose={()=>setUiAction(null)} onPin={()=>setUiAction(null)}/>
  </div>
}

function moduleForSource(source?:SourceMeta|null){
  const name=source?.doctype||source?.source_name||''
  if(/Stock|Item|Warehouse/i.test(name))return 'stock'
  if(/Purchase|Supplier|Buying/i.test(name))return 'buying'
  if(/Sales|Customer|Quotation|Lead|Opportunity/i.test(name))return 'selling'
  if(/Receivable|Payable|Ledger|Trial|Account/i.test(name))return 'accounting'
  if(/Project|Task/i.test(name))return 'projects'
  if(/Issue|Support/i.test(name))return 'support'
  return null
}

function EmptyCommandCenter({onPrompt}:{onPrompt:(prompt:string)=>void}){
  const [preview,setPreview]=useState<DocumentPreview|null>(null);const confirm=useConfirmDocumentDraft()
  return <div className="mx-auto flex min-h-full max-w-4xl flex-col items-center justify-center px-5 pb-28 pt-12"><TinniAvatar className="size-16 shadow-lg shadow-indigo-200"/><h1 className="mt-5 font-[Manrope] text-2xl font-bold">What would you like to do?</h1><p className="mt-2 text-center text-sm text-slate-500">Ask Tinni about ERPNext data, prepare a controlled draft action, or upload a business document for OCR intake.</p><div className="mt-8 grid w-full gap-3 sm:grid-cols-2">{prompts.map((prompt,index)=><button onClick={()=>onPrompt(prompt)} key={prompt} className="card flex items-start gap-3 p-4 text-left text-sm font-medium text-slate-700 transition hover:-translate-y-0.5 hover:border-indigo-200 hover:shadow-md"><span className="flex size-8 shrink-0 items-center justify-center rounded-lg bg-indigo-50 text-indigo-600">{index%2?<LayoutDashboard size={15}/>:<Sparkles size={15}/>}</span><span>{prompt}</span></button>)}</div><div className="mt-6 w-full">{preview?<DocumentMappingPreview preview={preview} busy={confirm.isPending} onConfirm={()=>confirm.mutate(preview.intake_id)} onCancel={()=>setPreview(null)}/>:<DocumentUploadPanel onProcessed={setPreview}/>}</div></div>
}

function HistoryMessage({message,onAction,onSuggestion,onRowClick}:{message:ChatMessage;onAction:(action:SuggestedAction,source?:SourceMeta|null)=>void;onSuggestion:(suggestion:SuggestedPrompt,source?:SourceMeta|null)=>void;onRowClick:(row:Record<string,unknown>)=>void}){
  if(message.role==='user')return <ChatBubble role="user">{message.content}</ChatBubble>
  if(message.role!=='assistant')return null
  const chart=message.parts?.find(part=>part.type==='chart');const chartConfig=chart&&chart.type==='chart'?{chart_type:chart.chart_type,x_key:chart.x_key,y_key:chart.y_key}:null
  return <ChatBubble role="assistant" extraction={message.extraction}><StructuredMessageParts parts={message.parts} fallback={message.content} source={message.source} permission={message.permission} actions={message.suggestedActions?.filter(action=>!['pin_to_dashboard','pin_overview'].includes(action.action_type))} onAction={onAction} onRowClick={onRowClick} actionSlot={message.source?<PinToDashboardButton conversationId={message.conversationId} messageId={message.id} source={message.source} chartConfig={chartConfig}/>:undefined}/><SuggestedPromptButtons suggestions={message.suggestions} onSuggestionClick={suggestion=>onSuggestion(suggestion,message.source)}/></ChatBubble>
}

function AssistantResponseView({response,onAction,onSuggestion,onRowClick}:{response:AssistantChatResponse;onAction:(action:SuggestedAction,source?:SourceMeta|null)=>void;onSuggestion:(suggestion:SuggestedPrompt,source?:SourceMeta|null)=>void;onRowClick:(row:Record<string,unknown>)=>void}){
  const chart=response.parts.find(part=>part.type==='chart');const chartConfig=chart&&chart.type==='chart'?{chart_type:chart.chart_type,x_key:chart.x_key,y_key:chart.y_key}:null
  return <ChatBubble role="assistant" extraction={response.extraction}><StructuredMessageParts parts={response.parts} fallback={response.content} source={response.source} permission={response.permission} actions={response.suggested_actions.filter(action=>!['pin_to_dashboard','pin_overview'].includes(action.action_type))} onAction={onAction} onRowClick={onRowClick} actionSlot={response.source?<PinToDashboardButton conversationId={response.conversation_id} messageId={response.message_id} source={response.source} chartConfig={chartConfig}/>:undefined}/><SuggestedPromptButtons suggestions={response.suggestions} onSuggestionClick={suggestion=>onSuggestion(suggestion,response.source)}/></ChatBubble>
}

function TypingIndicator(){return <span className="inline-flex gap-1.5"><span className="typing-dot size-1.5 rounded-full bg-indigo-500"/><span className="typing-dot size-1.5 rounded-full bg-indigo-500"/><span className="typing-dot size-1.5 rounded-full bg-indigo-500"/></span>}
