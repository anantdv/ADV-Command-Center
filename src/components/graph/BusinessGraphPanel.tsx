import { useEffect, useMemo, useState } from 'react'
import { GitBranch, Loader2, Network, RefreshCw } from 'lucide-react'
import { getRelatedDocuments } from '../../services/businessGraphService'
import type { GraphEdge, GraphNode, RelatedDocumentsResponse } from '../../types/businessGraph'

type Props = {
  doctype: string
  name: string
}

export function BusinessGraphPanel({ doctype, name }: Props) {
  const [open, setOpen] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [data, setData] = useState<RelatedDocumentsResponse | null>(null)

  async function load() {
    setLoading(true)
    setError(null)
    try {
      setData(await getRelatedDocuments(doctype, name, 1))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not load related documents.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (open && !data && !loading) void load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, doctype, name])

  const related = useMemo(() => {
    const graph = data?.related
    if (!graph) return []
    return graph.nodes.filter(node => node.id !== graph.root.id).slice(0, 12).map(node => ({
      node,
      edges: graph.edges.filter(edge => edge.source_id === node.id || edge.sourceId === node.id || edge.target_id === node.id || edge.targetId === node.id),
    }))
  }, [data])

  return <div className="border-t border-slate-100">
    <button type="button" onClick={() => setOpen(value => !value)} className="flex w-full items-center justify-between px-4 py-3 text-left text-xs font-bold text-slate-700 hover:bg-slate-50">
      <span className="inline-flex items-center gap-2"><Network size={14} className="text-violet-600"/>Business graph</span>
      <span className="text-[10px] font-semibold text-slate-400">{open ? 'Hide' : 'Show related documents'}</span>
    </button>
    {open && <div className="space-y-3 px-4 pb-4">
      {loading && <div className="flex items-center gap-2 rounded-xl bg-slate-50 px-3 py-3 text-xs text-slate-500"><Loader2 size={14} className="animate-spin"/>Discovering relationships…</div>}
      {error && <div className="rounded-xl border border-rose-100 bg-rose-50 px-3 py-2 text-xs font-semibold text-rose-700">{error}</div>}
      {!loading && !error && related.length === 0 && <div className="rounded-xl bg-slate-50 px-3 py-3 text-xs text-slate-500">No related documents were discovered from readable fields.</div>}
      {related.length > 0 && <div className="grid gap-2 sm:grid-cols-2">
        {related.map(({ node, edges }) => <RelatedNodeCard key={node.id} node={node} edges={edges}/>)}
      </div>}
      {data?.related.truncated && <p className="text-[10px] font-semibold text-amber-600">Some relationships were hidden because the graph limit was reached.</p>}
      <button type="button" onClick={load} disabled={loading} className="btn-secondary h-8 px-2 text-xs"><RefreshCw size={13}/>Refresh graph</button>
    </div>}
  </div>
}

function RelatedNodeCard({ node, edges }: { node: GraphNode; edges: GraphEdge[] }) {
  const nodeType = node.node_type || node.nodeType
  return <div className="rounded-xl border border-slate-100 bg-white p-3 shadow-sm">
    <div className="flex items-start gap-2">
      <span className="mt-0.5 flex size-7 shrink-0 items-center justify-center rounded-lg bg-violet-50 text-violet-600"><GitBranch size={13}/></span>
      <div className="min-w-0">
        <p className="truncate text-xs font-bold text-slate-800">{node.label || node.name}</p>
        <p className="mt-0.5 truncate text-[10px] font-semibold text-slate-400">{node.doctype} · {node.name}</p>
        <div className="mt-2 flex flex-wrap gap-1.5">
          <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[9px] font-bold uppercase tracking-wide text-slate-500">{nodeType}</span>
          {node.status && <span className="rounded-full bg-amber-50 px-2 py-0.5 text-[9px] font-bold text-amber-700">{node.status}</span>}
          {edges.slice(0, 2).map(edge => <span key={edge.id} className="rounded-full bg-indigo-50 px-2 py-0.5 text-[9px] font-bold text-indigo-600">{edge.edge_type || edge.edgeType}</span>)}
        </div>
      </div>
    </div>
  </div>
}
