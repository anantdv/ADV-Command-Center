import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { cancelAction, cancelCrudAction, confirmAction, confirmCrudAction, continueCrudAction, createConversation, getCommandCenterSeed, getConversationMessages, getConversations, sendChatMessage } from '../../services/chatService'
export const chatKeys={conversations:['chat','conversations'] as const,messages:(id:string)=>['chat','conversations',id,'messages'] as const,seed:['chat','seed'] as const}
export const useConversations=()=>useQuery({queryKey:chatKeys.conversations,queryFn:getConversations})
export const useConversationMessages=(id:string)=>useQuery({queryKey:chatKeys.messages(id),queryFn:()=>getConversationMessages(id),enabled:Boolean(id)})
export const useCommandCenterSeed=()=>useQuery({queryKey:chatKeys.seed,queryFn:getCommandCenterSeed})
export function useCreateConversation(){const client=useQueryClient();return useMutation({mutationFn:createConversation,onSuccess:()=>client.invalidateQueries({queryKey:chatKeys.conversations})})}
export function useSendChatMessage(){const client=useQueryClient();return useMutation({mutationFn:sendChatMessage,onSuccess:message=>{void client.invalidateQueries({queryKey:chatKeys.messages(message.conversation_id)});void client.invalidateQueries({queryKey:chatKeys.conversations})}})}
export const useConfirmAction=()=>useMutation({mutationFn:confirmAction})
export const useCancelAction=()=>useMutation({mutationFn:cancelAction})
export function useConfirmCrud(){const client=useQueryClient();return useMutation({mutationFn:confirmCrudAction,onSuccess:()=>client.invalidateQueries({queryKey:chatKeys.conversations})})}
export const useCancelCrud=()=>useMutation({mutationFn:cancelCrudAction})
export function useContinueCrud(){const client=useQueryClient();return useMutation({mutationFn:continueCrudAction,onSuccess:message=>{void client.invalidateQueries({queryKey:chatKeys.messages(message.conversation_id)});void client.invalidateQueries({queryKey:chatKeys.conversations})}})}
