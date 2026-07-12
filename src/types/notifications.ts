export interface NotificationTickerItem {
  id: string
  type: 'approval' | 'invoice' | 'issue' | 'task' | 'stock' | 'system' | 'event'
  label: string
  message: string
  priority: 'low' | 'medium' | 'high' | 'critical'
  route?: string | null
  createdAt?: string | null
}
