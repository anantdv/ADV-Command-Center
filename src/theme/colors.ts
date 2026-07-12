export const chartPalette = [
  '#6366F1',
  '#10B981',
  '#F59E0B',
  '#EF4444',
  '#06B6D4',
  '#8B5CF6',
  '#EC4899',
  '#84CC16',
  '#F97316',
  '#14B8A6',
]

export const moduleIconPalette: Record<string, string> = {
  Selling: '#6366F1',
  Buying: '#F59E0B',
  Stock: '#14B8A6',
  Accounts: '#10B981',
  Accounting: '#10B981',
  CRM: '#EC4899',
  Projects: '#8B5CF6',
  Support: '#EF4444',
  HR: '#06B6D4',
  Assets: '#84CC16',
  Manufacturing: '#F97316',
}

export function colorFromText(value: string, palette = chartPalette) {
  const sum = Array.from(value || 'ADV').reduce((acc, char) => acc + char.charCodeAt(0), 0)
  return palette[sum % palette.length]
}
