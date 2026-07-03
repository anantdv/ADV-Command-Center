import type { PermissionMeta } from './api'

export type Ticket = { id: string; subject: string; priority: 'High' | 'Medium' | 'Low'; status: 'Open' | 'In Progress' | 'Resolved'; assignedTo: string; created: string; permissions?: PermissionMeta }
export type SupportData = { tickets: Ticket[] }
export type CreateTicketRequest = { subject: string; description: string; priority: Ticket['priority'] }
import type { RAGCitation } from './knowledge'
export type AiHelpRequest = { message: string; module?: string; conversationId?:string }
export type AiHelpResponse = { answer: string; suggestedActions: string[]; createTicketRecommended: boolean; citations:RAGCitation[]; escalationRecommended:boolean; escalationReason?:string|null;suggestedTicketSubject?:string|null;suggestedTicketDescription?:string|null }
export type EscalateSupportRequest={question:string;aiAnswer?:string;citations?:RAGCitation[];subject:string;description:string;priority:'Low'|'Medium'|'High'|'Urgent';module?:string;conversationId?:string}
