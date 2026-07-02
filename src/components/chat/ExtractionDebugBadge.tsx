import { BrainCircuit } from 'lucide-react'
import type { ExtractionMeta } from '../../types/chat'

export function ExtractionDebugBadge({extraction}:{extraction?:ExtractionMeta|null}){
  if(!import.meta.env.DEV||!extraction)return null
  const label=extraction.method==='vertex_gemini'?'Extracted by Vertex Gemini':'Extracted by rules'
  return <span title={extraction.model||extraction.provider||extraction.method} className="inline-flex items-center gap-1 rounded-full bg-violet-50 px-2 py-1 text-[9px] font-bold text-violet-600"><BrainCircuit size={10}/>{label}{typeof extraction.confidence==='number'?` · ${Math.round(extraction.confidence*100)}%`:''}</span>
}
