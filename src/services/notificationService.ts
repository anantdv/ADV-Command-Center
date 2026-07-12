import { apiClient } from './apiClient'
import { env } from '../config/env'
import type { NotificationTickerItem } from '../types/notifications'

const mockItems: NotificationTickerItem[] = [
  { id: 'notif_approval', type: 'approval', label: 'Approvals', message: '3 documents waiting for review', priority: 'high', route: '/command-center?prompt=show%20my%20pending%20approvals&autoRun=true' },
  { id: 'notif_invoice', type: 'invoice', label: 'Receivables', message: '4 overdue sales invoices', priority: 'medium', route: '/command-center?prompt=show%20overdue%20sales%20invoices&autoRun=true' },
  { id: 'notif_stock', type: 'stock', label: 'Stock', message: '2 items may need attention', priority: 'low', route: '/modules/stock' },
]

export const getNotificationTicker = (): Promise<NotificationTickerItem[]> => env.useMockApi ? Promise.resolve(mockItems) : apiClient.get('/api/notifications/ticker')
