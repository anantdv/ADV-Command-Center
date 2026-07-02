import { Sparkles } from 'lucide-react'
import type { ReactNode } from 'react'
export function EmptyState({ title, description, action }: { title: string; description: string; action?: ReactNode }) { return <div className="card flex min-h-64 flex-col items-center justify-center p-8 text-center"><div className="mb-4 flex size-12 items-center justify-center rounded-2xl bg-indigo-50 text-indigo-600"><Sparkles /></div><h3 className="font-semibold">{title}</h3><p className="mt-2 max-w-sm text-sm text-slate-500">{description}</p>{action&&<div className="mt-5">{action}</div>}</div> }
