import { useEffect, useState } from 'react'
import { CommandInput } from '../chat/CommandInput'
import { ChatMessage as ChatBubble } from '../chat/ChatMessage'
import { StructuredMessageParts } from '../chat/StructuredMessageParts'
import { useSendChatMessage } from '../../hooks/api/useChat'
import type { AssistantChatResponse } from '../../types/chat'

export function ModuleBottomChat({ moduleName, seedPrompt }: { moduleName: string; seedPrompt?: string | null }) {
  const sendMessage = useSendChatMessage()
  const [thread,setThread]=useState<Array<{role:'user';content:string}|{role:'assistant';response:AssistantChatResponse}>>([])
  const send=(message:string)=>{
    if(!message.trim()||sendMessage.isPending)return
    setThread(items=>[...items,{role:'user',content:message}])
    sendMessage.mutate({message,module_context:moduleName},{onSuccess:response=>setThread(items=>[...items,{role:'assistant',response}])})
  }
  useEffect(()=>{
    if(seedPrompt&&!sendMessage.isPending) send(seedPrompt.replace(/\s+#\d+$/,'').trim())
    // eslint-disable-next-line react-hooks/exhaustive-deps
  },[seedPrompt])
  const rowClick=(row:Record<string,unknown>)=>{
    const meta=row._meta as {doctype?:string;name?:string;clickable?:boolean}|undefined
    if(meta?.doctype&&meta.name)send(`show detail for ${meta.doctype} ${meta.name}`)
  }
  return <div className="sticky bottom-0 z-10 border-t border-slate-200 bg-[#f8f9fc]/95 px-4 pb-4 pt-3 backdrop-blur">
    <div className="mx-auto max-w-5xl">
      {thread.length>0&&<div className="mb-3 max-h-80 space-y-3 overflow-y-auto rounded-2xl border border-slate-200 bg-white p-3 shadow-sm">
        {thread.map((item,index)=>item.role==='user'?<ChatBubble key={index} role="user">{item.content}</ChatBubble>:<ChatBubble key={index} role="assistant" extraction={item.response.extraction}><StructuredMessageParts parts={item.response.parts} fallback={item.response.content} source={item.response.source} permission={item.response.permission} actions={item.response.suggested_actions} onRowClick={rowClick}/></ChatBubble>)}
        {sendMessage.isError&&<ChatBubble role="assistant"><div className="rounded-xl border border-rose-100 bg-rose-50 p-3 text-xs font-semibold text-rose-700">{sendMessage.error instanceof Error?sendMessage.error.message:'The module command could not be completed.'}</div></ChatBubble>}
      </div>}
      <CommandInput onSend={send}/>
      <p className="mt-2 text-center text-[10px] text-slate-400">{moduleName} context enabled · ERPNext permissions always apply</p>
    </div>
  </div>
}
