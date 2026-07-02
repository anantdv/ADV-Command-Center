export interface AuthUser { user: string; fullName: string; email?: string; roles?: string[]; company?: string; companyCurrency?: string; allowedCompanies?: string[]; timezone?: string; language?: string }
export interface LoginRequest { username: string; password: string }
export interface LoginResponse extends AuthUser { message?: string }
export interface AuthMeResponse { authenticated: boolean; user: AuthUser | null }
