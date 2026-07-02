import { useMutation, useQuery } from '@tanstack/react-query'
import { getAllowedDoctypes, getCurrentUserContext, getDoctypeSchema, getRecord, listRecords } from '../../services/erpnextService'
export const erpnextKeys={context:['erpnext','context'] as const,doctypes:['erpnext','allowed-doctypes'] as const}
export const useCurrentUserContext=()=>useQuery({queryKey:erpnextKeys.context,queryFn:getCurrentUserContext})
export const useAllowedDoctypes=()=>useQuery({queryKey:erpnextKeys.doctypes,queryFn:getAllowedDoctypes})
export const useDoctypeSchema=()=>useMutation({mutationFn:getDoctypeSchema})
export const useListRecords=()=>useMutation({mutationFn:listRecords})
export const useGetRecord=()=>useMutation({mutationFn:getRecord})
