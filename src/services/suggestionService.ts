import { env } from '../config/env'
import type { AssistantChatResponse } from '../types/chat'
import type { SuggestedPrompt, SuggestionContext, SuggestionResponse } from '../types/suggestions'
import { apiClient } from './apiClient'

export const generateSuggestions=(context:SuggestionContext):Promise<SuggestionResponse> =>
  env.useMockApi ? Promise.resolve({ suggestions: [] }) : apiClient.post('/api/suggestions/generate', context)

export const executeSuggestion=(request:{suggestion:SuggestedPrompt;conversation_id?:string;conversationId?:string}):Promise<AssistantChatResponse|Record<string,unknown>> =>
  env.useMockApi ? Promise.resolve({}) : apiClient.post('/api/suggestions/execute', request)
