import type { ReactNode } from 'react'

export type Column<T> = { key: string; header: string; render: (row: T) => ReactNode; className?: string }
export function DataTable<T>({ columns, data, getKey }: { columns: Column<T>[]; data: T[]; getKey: (row: T) => string }) {
  return <div className="overflow-x-auto scrollbar-thin">
    <table className="w-full min-w-[680px] text-left">
      <thead><tr className="border-b border-slate-100">{columns.map(c => <th key={c.key} className={`px-4 py-3 text-[10px] font-bold uppercase tracking-wider text-slate-400 ${c.className || ''}`}>{c.header}</th>)}</tr></thead>
      <tbody>{data.map(row => <tr key={getKey(row)} className="border-b border-slate-100 last:border-0 hover:bg-slate-50/70">{columns.map(c => <td key={c.key} className={`px-4 py-3.5 text-sm text-slate-600 ${c.className || ''}`}>{c.render(row)}</td>)}</tr>)}</tbody>
    </table>
  </div>
}
