import { useAppStore } from '../store/useAppStore'

export const useGlobalDateRange = () => {
  const dateRange = useAppStore(state => state.dateRange)
  const setDateRange = useAppStore(state => state.setDateRange)
  return { dateRange, setDateRange }
}
