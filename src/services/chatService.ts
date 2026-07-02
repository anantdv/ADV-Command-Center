import { env } from '../config/env'
import type { AssistantChatResponse, ChatActionResponse, ChatMessage, CommandCenterData, Conversation, CreateConversationRequest, SendChatMessageRequest } from '../types/chat'
import type { CancelCrudResponse, ConfirmCrudResponse, ContinueCrudRequest } from '../types/crud'
import { apiClient } from './apiClient'
import { mockChatService } from './mock/mockChatService'
export const getConversations=():Promise<Conversation[]>=>env.useMockApi?mockChatService.getConversations():apiClient.get('/api/chat/conversations')
export const getConversationMessages=(id:string):Promise<ChatMessage[]>=>env.useMockApi?mockChatService.getConversationMessages(id):apiClient.get(`/api/chat/conversations/${encodeURIComponent(id)}/messages`)
export const createConversation=(request:CreateConversationRequest={}):Promise<Conversation>=>env.useMockApi?mockChatService.createConversation(request):apiClient.post('/api/chat/conversations',request)
export const sendChatMessage=(request:SendChatMessageRequest):Promise<AssistantChatResponse>=>env.useMockApi?mockChatService.sendChatMessage(request):apiClient.post('/api/chat/message',request)
export const confirmAction=(id:string):Promise<ChatActionResponse>=>env.useMockApi?mockChatService.confirmAction(id):apiClient.post(`/api/chat/actions/${encodeURIComponent(id)}/confirm`)
export const cancelAction=(id:string):Promise<ChatActionResponse>=>env.useMockApi?mockChatService.cancelAction(id):apiClient.post(`/api/chat/actions/${encodeURIComponent(id)}/cancel`)
export const confirmCrudAction=(confirmationId:string):Promise<ConfirmCrudResponse>=>env.useMockApi?mockChatService.confirmCrudAction(confirmationId):apiClient.post('/api/chat/actions/confirm',{confirmation_id:confirmationId})
export const cancelCrudAction=(confirmationId:string):Promise<CancelCrudResponse>=>env.useMockApi?mockChatService.cancelCrudAction(confirmationId):apiClient.post('/api/chat/actions/cancel',{confirmation_id:confirmationId})
export const continueCrudAction=(request:ContinueCrudRequest):Promise<AssistantChatResponse>=>env.useMockApi?mockChatService.continueCrudAction(request):apiClient.post('/api/chat/actions/continue-crud',request)
export const getCommandCenterSeed=():Promise<CommandCenterData>=>env.useMockApi?mockChatService.getSeed():apiClient.get('/api/chat/seed')
export async function* streamChatMessage(request:SendChatMessageRequest):AsyncGenerator<AssistantChatResponse>{
  // TODO: Replace this compatibility generator with Server-Sent Events or WebSocket streaming from FastAPI.
  yield await sendChatMessage(request)
}
