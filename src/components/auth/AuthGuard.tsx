import { useEffect, type ReactNode } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { Bot } from 'lucide-react'
import { useAuthStore } from '../../store/useAuthStore'

export function AuthGuard({ children }: { children: ReactNode }) {
  const { user, checking, checkSession } = useAuthStore()
  const location = useLocation()
  useEffect(() => { void checkSession() }, [checkSession])

  if (checking) return <div className="grid min-h-screen place-items-center bg-slate-950"><div className="text-center"><div className="mx-auto flex size-12 items-center justify-center rounded-2xl bg-gradient-to-br from-indigo-500 to-violet-600 text-white"><Bot size={22}/></div><div className="mx-auto mt-5 size-6 animate-spin rounded-full border-2 border-slate-700 border-t-indigo-400"/><p className="mt-3 text-xs text-slate-400">Verifying ERPNext session…</p></div></div>
  if (!user) return <Navigate to="/login" replace state={{ from: location.pathname }} />
  return children
}
