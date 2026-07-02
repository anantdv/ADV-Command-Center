import type { AuthMeResponse, LoginRequest, LoginResponse } from '../../types/auth'
import { mockDelay } from './mockUtils'

const key = 'erp-ai-mock-user'
const mockUser: LoginResponse = { user: 'admin@abccorp.in', fullName: 'Admin User', email: 'admin@abccorp.in', roles: ['System Manager'], company:'ABC Corporation',companyCurrency:'INR',allowedCompanies:['ABC Corporation'],timezone:'Asia/Kolkata', message: 'Mock session active' }
export async function mockLogin(request: LoginRequest) { if (!request.username || !request.password) throw new Error('Username and password are required.'); sessionStorage.setItem(key, JSON.stringify({ ...mockUser, user: request.username })); return mockDelay({ ...mockUser, user: request.username }) }
export async function mockGetCurrentUser(): Promise<AuthMeResponse> { const stored = sessionStorage.getItem(key); return mockDelay({ authenticated: Boolean(stored), user: stored ? JSON.parse(stored) as LoginResponse : null }) }
export async function mockLogout() { sessionStorage.removeItem(key); return mockDelay(undefined) }
