import {useQuery} from '@tanstack/react-query'
import {communicationApi} from '../services/communicationApi'
export const useCommunicationThread=(name?:string)=>useQuery({queryKey:['communications','thread',name],queryFn:()=>communicationApi.thread(name!),enabled:Boolean(name)})
