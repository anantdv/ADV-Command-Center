import { useEffect, type ReactNode } from 'react'
import { QueryClientProvider } from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'
import { useAuthStore } from '../store/useAuthStore'
import { queryClient } from './queryClient'

function SessionExpiryListener() {
  const logout = useAuthStore(state => state.logout)
  useEffect(() => {
    const handleExpiry = async () => {
      await logout()
      if (window.location.pathname !== '/login') window.location.assign('/login')
    }
    window.addEventListener('erp-session-expired', handleExpiry)
    return () => window.removeEventListener('erp-session-expired', handleExpiry)
  }, [logout])
  return null
}

export function AppProviders({children}:{children:ReactNode}){return <QueryClientProvider client={queryClient}><SessionExpiryListener/>{children}{import.meta.env.DEV&&<ReactQueryDevtools initialIsOpen={false}/>}</QueryClientProvider>}
