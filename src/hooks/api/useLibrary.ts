import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { createLibraryFile, deleteLibraryFile, getLibraryFiles } from '../../services/libraryService'
export const libraryKeys={all:['library','files'] as const,list:(category?:string)=>['library','files',category||'all'] as const}
export const useLibraryFiles=(category?:string)=>useQuery({queryKey:libraryKeys.list(category),queryFn:()=>getLibraryFiles(category)})
export function useCreateLibraryFile(){const client=useQueryClient();return useMutation({mutationFn:createLibraryFile,onSuccess:()=>client.invalidateQueries({queryKey:libraryKeys.all})})}
export function useDeleteLibraryFile(){const client=useQueryClient();return useMutation({mutationFn:deleteLibraryFile,onSuccess:()=>client.invalidateQueries({queryKey:libraryKeys.all})})}
