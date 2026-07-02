import type { ReactNode } from 'react'
import { Sparkles } from 'lucide-react'
import { TinniAvatar } from '../common/BrandLogo'
import { ExtractionDebugBadge } from './ExtractionDebugBadge'
import type { ExtractionMeta } from '../../types/chat'
export function ChatMessage({ role, children, extraction }: { role: 'user' | 'assistant'; children: ReactNode; extraction?:ExtractionMeta|null }) {
  if (role === 'user') return <div className="flex justify-end"><div className="max-w-[85%] rounded-2xl rounded-br-md bg-slate-900 px-4 py-3 text-sm leading-6 text-white shadow-sm">{children}</div></div>
  return <div className="flex items-start gap-3"><TinniAvatar className="mt-0.5 size-9"/><div className="min-w-0 flex-1"><div className="mb-2 flex flex-wrap items-center gap-2"><p className="flex items-center gap-1.5 text-[11px] font-bold text-slate-500">Tinni <Sparkles size={10} className="text-indigo-500" /></p><ExtractionDebugBadge extraction={extraction}/></div><div className="text-sm leading-6 text-slate-700">{children}</div></div></div>
}
