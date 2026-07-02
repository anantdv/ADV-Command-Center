import { env } from '../config/env'
import type { ApiErrorShape } from '../types/api'

export class ApiClientError extends Error implements ApiErrorShape {
  constructor(public status: number, message: string, public details?: unknown) {
    super(message)
    this.name = 'ApiClientError'
  }
}

class ApiClient {
  private bearerToken?: string

  setBearerToken(token?: string) { this.bearerToken = token }

  private async request<T>(url: string, init: RequestInit = {}): Promise<T> {
    const controller = new AbortController()
    const timeout = window.setTimeout(() => controller.abort(), 30_000)
    try {
      const response = await fetch(`${env.apiBaseUrl}${url}`, {
        ...init,
        credentials: 'include',
        signal: controller.signal,
        headers: {
          Accept: 'application/json',
          'Content-Type': 'application/json',
          ...(this.bearerToken ? { Authorization: `Bearer ${this.bearerToken}` } : {}),
          ...init.headers,
        },
      })
      const payload = await response.json().catch(() => null) as { success?: boolean; data?: unknown; detail?: string; message?: string; details?: unknown } | null
      if (!response.ok) {
        const isAuthBootstrap = url.startsWith('/api/auth/')
        if (response.status === 401 && !isAuthBootstrap) window.dispatchEvent(new Event('erp-session-expired'))
        throw new ApiClientError(response.status, payload?.detail || payload?.message || `Request failed (${response.status})`, payload)
      }
      if (payload && typeof payload === 'object' && 'success' in payload && 'data' in payload) {
        if (payload.success === false) throw new ApiClientError(response.status, payload.message || 'The API request failed.', payload.details)
        return payload.data as T
      }
      return payload as T
    } catch (error) {
      if (error instanceof DOMException && error.name === 'AbortError') throw new ApiClientError(408, 'The request timed out.')
      if (error instanceof ApiClientError) throw error
      throw new ApiClientError(0, error instanceof Error ? error.message : 'Unable to reach the API.', error)
    } finally { window.clearTimeout(timeout) }
  }

  get<T>(url: string): Promise<T> { return this.request<T>(url) }
  post<T>(url: string, body?: unknown): Promise<T> { return this.request<T>(url, { method: 'POST', body: body === undefined ? undefined : JSON.stringify(body) }) }
  put<T>(url: string, body?: unknown): Promise<T> { return this.request<T>(url, { method: 'PUT', body: body === undefined ? undefined : JSON.stringify(body) }) }
  delete<T>(url: string): Promise<T> { return this.request<T>(url, { method: 'DELETE' }) }
}

export const apiClient = new ApiClient()
