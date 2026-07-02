import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { createSupportTicket, getSupportTickets, requestAiHelp } from '../../services/supportService'
export const supportKeys={tickets:['support','tickets'] as const}
export const useSupportTickets=()=>useQuery({queryKey:supportKeys.tickets,queryFn:getSupportTickets})
export function useCreateSupportTicket(){const client=useQueryClient();return useMutation({mutationFn:createSupportTicket,onSuccess:()=>client.invalidateQueries({queryKey:supportKeys.tickets})})}
export const useAiHelp=()=>useMutation({mutationFn:requestAiHelp})
