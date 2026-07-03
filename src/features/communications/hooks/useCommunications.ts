import {useQuery} from '@tanstack/react-query'
import {communicationApi} from '../services/communicationApi'
import type {MailFolder} from '../types/communication.types'
export const useCommunications=(folder:MailFolder,search:string,filters:Record<string,unknown>)=>useQuery({queryKey:['communications',folder,search,filters],queryFn:()=>communicationApi.list({folder,search,...filters}),staleTime:30_000})
