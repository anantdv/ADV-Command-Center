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

  private async request<T>(url: string, init: RequestInit = {}, timeoutMs = 30_000): Promise<T> {
    const controller = new AbortController()
    const timeout = window.setTimeout(() => controller.abort(), timeoutMs)
    try {
      const response = await fetch(`${env.apiBaseUrl}${url}`, {
        ...init,
        credentials: 'include',
        signal: controller.signal,
        headers: {
          Accept: 'application/json',
          ...(!(init.body instanceof FormData) ? { 'Content-Type': 'application/json' } : {}),
          ...(this.bearerToken ? { Authorization: `Bearer ${this.bearerToken}` } : {}),
          ...init.headers,
        },
      })
      const payload = await parseApiResponse(response, url) as { success?: boolean; data?: unknown; detail?: string; message?: string; details?: unknown; error?: { user_message?: string; debug_message?: string; code?: string } } | null
      if (!response.ok) {
        const isAuthBootstrap = url.startsWith('/api/auth/')
        if (response.status === 401 && !isAuthBootstrap) window.dispatchEvent(new Event('erp-session-expired'))
        throw new ApiClientError(response.status, payload?.error?.user_message || payload?.detail || payload?.message || `Request failed (${response.status})`, payload)
      }
      if (payload && typeof payload === 'object' && 'success' in payload && 'data' in payload) {
        if (payload.success === false) throw new ApiClientError(response.status, payload.error?.user_message || payload.message || 'The API request failed.', payload.error || payload.details)
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
  post<T>(url: string, body?: unknown, timeoutMs?: number): Promise<T> { return this.request<T>(url, { method: 'POST', body: body === undefined ? undefined : JSON.stringify(body) }, timeoutMs) }
  postForm<T>(url: string, formData: FormData, timeoutMs?: number): Promise<T> { return this.request<T>(url, { method: 'POST', body: formData }, timeoutMs) }
  put<T>(url: string, body?: unknown): Promise<T> { return this.request<T>(url, { method: 'PUT', body: body === undefined ? undefined : JSON.stringify(body) }) }
  delete<T>(url: string): Promise<T> { return this.request<T>(url, { method: 'DELETE' }) }
}

export const apiClient = new ApiClient()

async function parseApiResponse(response: Response, url: string) {
  const contentType = response.headers.get('content-type') || ''
  if (contentType.includes('application/json')) return response.json()
  const text = await response.text()
  throw new ApiClientError(
    response.status,
    'The server returned an invalid response. Please check backend API routing.',
    {
      url,
      contentType,
      rawPreview: text.slice(0, 300),
    },
  )
}
