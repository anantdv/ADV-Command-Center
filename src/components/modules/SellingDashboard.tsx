import type { ModuleDashboard, ModuleRecentDocument } from '../../types/module'
import { ModuleKpiCard } from './ModuleKpiCard'
import { ModuleQuickActions } from './ModuleQuickActions'
import { ModuleRecentDocuments } from './ModuleRecentDocuments'
import { ModuleReportCard } from './ModuleReportCard'

export function SellingDashboard({ dashboard, onPrompt }: { dashboard: ModuleDashboard; onPrompt: (prompt: string) => void }) {
  const openDocument=(doc:ModuleRecentDocument)=>onPrompt(`show detail for ${doc.doctype} ${doc.name}`)
  return <div className="space-y-6">
    <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">{dashboard.kpis.map(kpi=><ModuleKpiCard key={kpi.id} kpi={kpi} onClick={onPrompt}/>)}</div>
    <div className="grid gap-5 xl:grid-cols-2">{dashboard.reports.map(report=><ModuleReportCard key={report.id} report={report} onPrompt={onPrompt}/>)}</div>
    <div className="grid gap-5 xl:grid-cols-3">
      <div className="xl:col-span-2"><ModuleRecentDocuments documents={dashboard.recentDocuments} onOpen={openDocument}/></div>
      <ModuleQuickActions actions={dashboard.quickActions} onPrompt={onPrompt}/>
    </div>
  </div>
}
