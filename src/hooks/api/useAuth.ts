import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { getCurrentUser, login, logout } from '../../services/authService'
export const authKeys={me:['auth','me'] as const}
export const useCurrentUser=()=>useQuery({queryKey:authKeys.me,queryFn:getCurrentUser})
export function useLogin(){const client=useQueryClient();return useMutation({mutationFn:login,onSuccess:()=>client.invalidateQueries({queryKey:authKeys.me})})}
export function useLogout(){const client=useQueryClient();return useMutation({mutationFn:logout,onSuccess:()=>client.clear()})}
