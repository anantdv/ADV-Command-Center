export function ModulePinnedCards({ widgets = [] }: { widgets?: Array<Record<string, unknown>> }) {
  return <section>
    <div className="mb-3"><h2 className="text-sm font-bold text-slate-900">Pinned to this module</h2><p className="mt-1 text-xs text-slate-400">Saved analytics and report shortcuts for this workspace.</p></div>
    {widgets.length===0?<div className="rounded-2xl border border-dashed border-slate-200 bg-white p-6 text-center text-xs text-slate-400">No cards pinned to this module yet. Pin useful Command Center results here.</div>:<div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">{widgets.map((widget,index)=><article key={String(widget.widget_id||index)} className="card p-4"><p className="text-sm font-bold text-slate-800">{String(widget.title||'Pinned widget')}</p><p className="mt-1 text-[10px] text-slate-400">Refreshes through your ERPNext permissions.</p></article>)}</div>}
  </section>
}
