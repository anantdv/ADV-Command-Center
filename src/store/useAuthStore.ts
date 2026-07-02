import { create } from 'zustand'
import { getCurrentUser, login, logout } from '../services/authService'
import type { AuthUser } from '../types/auth'

type AuthState = {
  user: AuthUser | null
  checking: boolean
  error: string | null
  checkSession: () => Promise<void>
  login: (username: string, password: string) => Promise<boolean>
  logout: () => Promise<void>
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  checking: true,
  error: null,
  checkSession: async () => {
    try { const session=await getCurrentUser();set({ user: session.authenticated ? session.user : null, checking: false }) }
    catch { set({ user: null, checking: false }) }
  },
  login: async (username, password) => {
    set({ checking: true, error: null })
    try {
      const loginUser = await login({ username, password })
      const session = await getCurrentUser().catch(()=>({authenticated:true,user:loginUser}))
      set({ user: session.authenticated ? session.user : loginUser, checking: false })
      return true
    } catch (error) {
      set({ user: null, checking: false, error: error instanceof Error ? error.message : 'Login failed.' })
      return false
    }
  },
  logout: async () => {
    await logout().catch(() => undefined)
    set({ user: null, error: null })
  },
}))
