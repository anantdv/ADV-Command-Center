import { invoices } from '../../data/mockData'
import type { AssistantChatResponse, ChatActionResponse, ChatMessage, Conversation, CreateConversationRequest, SendChatMessageRequest } from '../../types/chat'
import type { ContinueCrudRequest } from '../../types/crud'
import { mockDelay } from './mockUtils'

let conversations:Conversation[]=[{id:'conv-welcome',title:'Welcome — ask Tinni about your ERP',createdAt:'2026-07-01T05:00:00Z',updatedAt:'2026-07-01T05:12:00Z'}]
const messages:Record<string,ChatMessage[]>={ 'conv-welcome':[] }

export const mockChatService={
  getConversations:()=>mockDelay(conversations),
  getConversationMessages:(id:string)=>mockDelay(messages[id]||[]),
  createConversation:(request:CreateConversationRequest)=>{const now=new Date().toISOString();const conversation={id:`conv-${Date.now()}`,title:request.title||'New command',createdAt:now,updatedAt:now};conversations=[conversation,...conversations];messages[conversation.id]=[];return mockDelay(conversation)},
  sendChatMessage:(request:SendChatMessageRequest):Promise<AssistantChatResponse>=>{const now=new Date().toISOString();const conversationId=request.conversation_id||`conv-${Date.now()}`;const response:AssistantChatResponse={conversation_id:conversationId,message_id:`msg-${Date.now()}`,id:`msg-${Date.now()}`,role:'assistant',intent:'unsupported',content:'Mock read-only analysis prepared.',created_at:now,parts:[{type:'text',content:'Mock read-only analysis prepared.'}],source:null,permission:{allowed:true,risk_level:'low',confirmation_required:false,filtered_fields:[],blocked_fields:[]},suggested_actions:[]};return mockDelay(response,350)},
  confirmAction:(id:string):Promise<ChatActionResponse>=>mockDelay({actionId:id,status:'confirmed'}),
  cancelAction:(id:string):Promise<ChatActionResponse>=>mockDelay({actionId:id,status:'cancelled'}),
  confirmCrudAction:(id:string)=>mockDelay({operation:'create' as const,doctype:'Customer',record_name:'MOCK-CUSTOMER',status:'Created',message:'Customer MOCK-CUSTOMER has been created successfully.',data:{name:'MOCK-CUSTOMER'}}),
  cancelCrudAction:(_id:string)=>mockDelay({cancelled:true}),
  continueCrudAction:(request:ContinueCrudRequest):Promise<AssistantChatResponse>=>{const now=new Date().toISOString();return mockDelay({conversation_id:request.conversation_id||'conv-mock',message_id:`msg-${Date.now()}`,id:`msg-${Date.now()}`,role:'assistant',intent:`crud_${request.operation}`,content:'Draft preview prepared.',created_at:now,parts:[{type:'text',content:'Draft preview prepared.'}],source:null,permission:{allowed:true,risk_level:'medium',confirmation_required:true,filtered_fields:[],blocked_fields:[]},suggested_actions:[]})},
  getSeed:()=>mockDelay({invoices}),
}
