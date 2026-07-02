import { env } from '../config/env'
import type { AiHelpRequest, AiHelpResponse, CreateTicketRequest, Ticket } from '../types/support'
import { apiClient } from './apiClient'
import { mockSupportService } from './mock/mockSupportService'
export const getSupportTickets=():Promise<Ticket[]>=>env.useMockApi?mockSupportService.getTickets():apiClient.get('/api/support/tickets')
export const createSupportTicket=(request:CreateTicketRequest):Promise<Ticket>=>env.useMockApi?mockSupportService.createTicket(request):apiClient.post('/api/support/tickets',request)
export const requestAiHelp=(request:AiHelpRequest):Promise<AiHelpResponse>=>env.useMockApi?mockSupportService.getAiHelp(request):apiClient.post('/api/support/ai-help',request)
