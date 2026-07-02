import 'dotenv/config'

const normalizeUrl = (value: string) => value.replace(/\/+$/, '')

export const config = {
  erpServerUrl: normalizeUrl(process.env.ERP_SERVER_URL || 'https://courtsdemo.advtinni.com'),
  port: Number(process.env.BACKEND_PORT || 3001),
  isProduction: process.env.NODE_ENV === 'production',
  sessionMaxAgeMs: 3 * 24 * 60 * 60 * 1000,
}

if (!config.erpServerUrl.startsWith('https://')) {
  throw new Error('ERP_SERVER_URL must use HTTPS')
}
