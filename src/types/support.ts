import type { PermissionMeta } from './api'

export type Ticket = { id: string; subject: string; priority: 'High' | 'Medium' | 'Low'; status: 'Open' | 'In Progress' | 'Resolved'; assignedTo: string; created: string; permissions?: PermissionMeta }
export type SupportData = { tickets: Ticket[] }
export type CreateTicketRequest = { subject: string; description: string; priority: Ticket['priority'] }
export type AiHelpRequest = { message: string; module?: string }
export type AiHelpResponse = { answer: string; suggestedActions: string[]; createTicketRecommended: boolean }
