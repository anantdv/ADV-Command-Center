const required = (value: string | undefined, fallback: string) => (value || fallback).replace(/\/$/, '')

export const env = {
  apiBaseUrl: required(import.meta.env.VITE_API_BASE_URL, 'http://localhost:8000'),
  useMockApi: import.meta.env.VITE_USE_MOCK_API !== 'false',
  erpSiteUrl: required(import.meta.env.VITE_ERP_SITE_URL, 'http://localhost:8000'),
  appName: import.meta.env.VITE_APP_NAME || 'ADV Command Center',
} as const
