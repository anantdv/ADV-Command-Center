import { useQuery } from '@tanstack/react-query'
import { getNotificationTicker } from '../../services/notificationService'

export const notificationKeys = { ticker: ['notifications', 'ticker'] as const }
export const useNotificationTicker = () => useQuery({ queryKey: notificationKeys.ticker, queryFn: getNotificationTicker, refetchInterval: 60000 })
