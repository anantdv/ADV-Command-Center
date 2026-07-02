import express, { type Request, type Response } from 'express'
import { config } from './config.js'

const app = express()
app.disable('x-powered-by')
app.use(express.json({ limit: '2mb' }))
app.use(express.urlencoded({ extended: false }))

const cookieValue = (req: Request, name: string) => {
  const cookie = req.headers.cookie?.split(';').map((part) => part.trim()).find((part) => part.startsWith(`${name}=`))
  return cookie ? decodeURIComponent(cookie.slice(name.length + 1)) : undefined
}

const erpFetch = (path: string, options: RequestInit = {}) => fetch(`${config.erpServerUrl}${path}`, {
  ...options,
  headers: { Accept: 'application/json', ...options.headers },
  redirect: 'manual',
})

const sendUpstream = async (response: globalThis.Response, res: Response) => {
  const contentType = response.headers.get('content-type')
  const disposition = response.headers.get('content-disposition')
  if (contentType) res.setHeader('content-type', contentType)
  if (disposition) res.setHeader('content-disposition', disposition)
  res.status(response.status).send(Buffer.from(await response.arrayBuffer()))
}

app.get('/api/health', (_req, res) => res.json({ ok: true, erpConfigured: true }))

app.post('/api/auth/login', async (req, res) => {
  const { username, password } = req.body as { username?: string; password?: string }
  if (!username?.trim() || !password) return res.status(400).json({ message: 'Username and password are required.' })

  try {
    const response = await erpFetch('/api/method/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ usr: username.trim(), pwd: password }),
    })
    const payload = await response.json().catch(() => ({})) as Record<string, unknown>
    if (!response.ok) return res.status(response.status).json({ message: 'Invalid ERPNext username or password.' })

    const getSetCookie = (response.headers as Headers & { getSetCookie?: () => string[] }).getSetCookie?.bind(response.headers)
    const setCookies = getSetCookie ? getSetCookie() : [response.headers.get('set-cookie') || '']
    const sidMatch = setCookies.join(',').match(/(?:^|[,;]\s*)sid=([^;,]+)/)
    if (!sidMatch?.[1]) return res.status(502).json({ message: 'ERPNext did not return a valid session.' })

    res.cookie('sid', sidMatch[1], {
      httpOnly: true,
      secure: config.isProduction,
      sameSite: 'lax',
      path: '/',
      maxAge: config.sessionMaxAgeMs,
    })
    return res.json({
      user: username.trim(),
      fullName: String(payload.full_name || username.trim()),
      message: String(payload.message || 'Logged in'),
    })
  } catch {
    return res.status(502).json({ message: 'Unable to reach the ERPNext server.' })
  }
})

app.get('/api/auth/session', async (req, res) => {
  const sid = cookieValue(req, 'sid')
  if (!sid) return res.status(401).json({ authenticated: false })
  try {
    const response = await erpFetch('/api/method/frappe.auth.get_logged_user', { headers: { Cookie: `sid=${sid}` } })
    if (!response.ok) {
      res.clearCookie('sid', { path: '/' })
      return res.status(401).json({ authenticated: false })
    }
    const payload = await response.json() as { message?: string }
    return res.json({ authenticated: true, user: payload.message || 'User' })
  } catch {
    return res.status(502).json({ message: 'Unable to verify the ERPNext session.' })
  }
})

app.post('/api/auth/logout', async (req, res) => {
  const sid = cookieValue(req, 'sid')
  if (sid) {
    await erpFetch('/api/method/logout', { method: 'GET', headers: { Cookie: `sid=${sid}` } }).catch(() => undefined)
  }
  res.clearCookie('sid', { path: '/' })
  return res.status(204).send()
})

// Authenticated Frappe proxy. Example: /api/erp/api/resource/Sales%20Invoice
app.use('/api/erp', async (req, res) => {
  const sid = cookieValue(req, 'sid')
  if (!sid) return res.status(401).json({ message: 'ERPNext session required.' })
  const upstreamPath = req.originalUrl.slice('/api/erp'.length)
  if (!upstreamPath.startsWith('/api/')) return res.status(400).json({ message: 'Only Frappe API paths are allowed.' })

  try {
    const hasBody = !['GET', 'HEAD'].includes(req.method)
    const response = await erpFetch(upstreamPath, {
      method: req.method,
      headers: {
        Cookie: `sid=${sid}`,
        ...(req.headers['content-type'] ? { 'Content-Type': req.headers['content-type'] } : {}),
      },
      body: hasBody && req.body !== undefined ? JSON.stringify(req.body) : undefined,
    })
    if (response.status === 401 || response.status === 403) res.clearCookie('sid', { path: '/' })
    return sendUpstream(response, res)
  } catch {
    return res.status(502).json({ message: 'ERPNext API request failed.' })
  }
})

app.listen(config.port, '127.0.0.1', () => {
  console.log(`Backend listening on http://127.0.0.1:${config.port}`)
  console.log(`ERPNext target: ${config.erpServerUrl}`)
})
