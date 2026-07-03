import { BookOpenCheck } from 'lucide-react'
import type { KnowledgeSourceType } from '../../types/knowledge'
export function KnowledgeSourceBadge({type}:{type:KnowledgeSourceType}){return <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2 py-1 text-[10px] font-bold text-emerald-700"><BookOpenCheck size={11}/>{type.replaceAll('_',' ')}</span>}
