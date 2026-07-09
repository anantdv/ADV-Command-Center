import { useNavigate, useParams } from 'react-router-dom'
import { ErrorState } from '../../components/common/ErrorState'
import { LoadingState } from '../../components/common/LoadingState'
import { ModuleDoctypeNavigation } from '../../components/modules/ModuleDoctypeNavigation'
import { ModuleHeader } from '../../components/modules/ModuleHeader'
import { ModuleKpiCard } from '../../components/modules/ModuleKpiCard'
import { ModulePinnedCards } from '../../components/modules/ModulePinnedCards'
import { ModuleQuickActions } from '../../components/modules/ModuleQuickActions'
import { ModuleRecentDocuments } from '../../components/modules/ModuleRecentDocuments'
import { ModuleReportCard } from '../../components/modules/ModuleReportCard'
import { useModuleDashboard, useModuleDoctypes } from '../../hooks/api/useModules'
import type { ModuleRecentDocument } from '../../types/module'

export function ModuleWorkspacePage(){
  const {moduleName='Selling'}=useParams()
  const navigate=useNavigate()
  const dashboard=useModuleDashboard(moduleName)
  const doctypes=useModuleDoctypes(moduleName)
  const sendPrompt=(value:string)=>navigate(`/command-center?module=${encodeURIComponent(dashboard.data?.label||moduleName)}&prompt=${encodeURIComponent(value)}&autoRun=true`)
  const openDocument=(doc:ModuleRecentDocument)=>sendPrompt(`show detail for ${doc.doctype} ${doc.name}`)
  if(dashboard.isLoading)return <LoadingState cards={5}/>
  if(dashboard.isError||!dashboard.data)return <ErrorState retry={()=>void dashboard.refetch()} message={`I could not load the ${moduleName} module dashboard.`}/>
  return <div className="-m-4 min-h-[calc(100vh-72px)] bg-[#f8f9fc] p-4 sm:-m-6 sm:p-6 lg:-m-8 lg:p-8">
    <main className="space-y-6">
      <ModuleHeader label={dashboard.data.label} doctypes={dashboard.data.doctypes} onAskAi={()=>navigate(`/command-center?module=${encodeURIComponent(dashboard.data.label)}`)}/>
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">{dashboard.data.kpis.map(kpi=><ModuleKpiCard key={kpi.id} kpi={kpi} onClick={sendPrompt}/>)}</div>
      <ModulePinnedCards widgets={dashboard.data.pinnedWidgets}/>
      <div className="grid gap-5 xl:grid-cols-2">{dashboard.data.reports.map(report=><ModuleReportCard key={report.id} report={report} onPrompt={sendPrompt}/>)}</div>
      <ModuleDoctypeNavigation moduleName={dashboard.data.label} doctypes={doctypes.data?.doctypes||[]}/>
      <div className="grid gap-5 xl:grid-cols-3">
        <div className="xl:col-span-2"><ModuleRecentDocuments documents={dashboard.data.recentDocuments} onOpen={openDocument}/></div>
        <ModuleQuickActions actions={dashboard.data.quickActions} onPrompt={sendPrompt}/>
      </div>
    </main>
  </div>
}
