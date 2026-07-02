export const formatCurrency = (value: number, currency = 'INR') => new Intl.NumberFormat('en-IN', {
  style: 'currency', currency, maximumFractionDigits: 0,
}).format(value)
export const formatINR = (value:number)=>formatCurrency(value,'INR')

export const formatDate = (value: string) => new Intl.DateTimeFormat('en-IN', {
  day: '2-digit', month: 'short', year: 'numeric',
}).format(new Date(value))
