import { env } from '../config/env'
import type { AuthMeResponse, AuthUser, LoginRequest, LoginResponse } from '../types/auth'
import { apiClient } from './apiClient'
import { mockGetCurrentUser, mockLogin, mockLogout } from './mock/mockAuthService'

export const login = (request: LoginRequest): Promise<LoginResponse> => env.useMockApi ? mockLogin(request) : apiClient.post('/api/auth/login', request)
export async function getCurrentUser():Promise<AuthMeResponse>{if(env.useMockApi)return mockGetCurrentUser();const user=await apiClient.get<AuthUser>('/api/auth/me');return{authenticated:true,user}}
export const logout = (): Promise<void> => env.useMockApi ? mockLogout() : apiClient.post('/api/auth/logout')
