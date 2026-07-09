import { useParams } from 'react-router-dom'
import { useNavigate } from 'react-router-dom'
import { ErrorState } from '../../components/common/ErrorState'
import { LoadingState } from '../../components/common/LoadingState'
import { ModuleDoctypeNavigation } from '../../components/modules/ModuleDoctypeNavigation'
import { ModuleHeader } from '../../components/modules/ModuleHeader'
import { ModuleKpiCard } from '../../components/modules/ModuleKpiCard'
import { ModulePinnedCards } from '../../components/modules/ModulePinnedCards'
import { ModuleQuickActions } from '../../components/modules/ModuleQuickActions'
import { useModuleDashboard, useModuleDoctypes } from '../../hooks/api/useModules'

export function ModuleWorkspacePage(){
  const {moduleName='Selling'}=useParams()
  const navigate=useNavigate()
  const dashboard=useModuleDashboard(moduleName)
  const doctypes=useModuleDoctypes(moduleName)
  const sendPrompt=(value:string)=>navigate(`/command-center?module=${encodeURIComponent(dashboard.data?.label||moduleName)}&prompt=${encodeURIComponent(value)}&autoRun=true`)
  if(dashboard.isLoading)return <LoadingState cards={5}/>
  if(dashboard.isError||!dashboard.data)return <ErrorState retry={()=>void dashboard.refetch()} message={`I could not load the ${moduleName} module dashboard.`}/>
  return <div className="-m-4 min-h-[calc(100vh-72px)] bg-[#f8f9fc] p-4 sm:-m-6 sm:p-6 lg:-m-8 lg:p-8">
    <main className="space-y-6">
      <ModuleHeader label={dashboard.data.label} doctypes={dashboard.data.doctypes} onAskAi={()=>navigate(`/command-center?module=${encodeURIComponent(dashboard.data.label)}`)}/>
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">{dashboard.data.kpis.map(kpi=><ModuleKpiCard key={kpi.id} kpi={kpi} onClick={sendPrompt}/>)}</div>
      <ModulePinnedCards widgets={dashboard.data.pinnedWidgets}/>
      <ModuleDoctypeNavigation moduleName={dashboard.data.label} doctypes={doctypes.data?.doctypes||[]}/>
      <div className="grid gap-5 xl:grid-cols-3">
        <section className="card p-5 xl:col-span-2"><h3 className="text-sm font-bold text-slate-900">Permitted DocTypes</h3><div className="mt-4 flex flex-wrap gap-2">{dashboard.data.doctypes.map(doctype=><span key={doctype} className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-semibold text-slate-600">{doctype}</span>)}</div></section>
        <ModuleQuickActions actions={dashboard.data.quickActions} onPrompt={sendPrompt}/>
      </div>
    </main>
  </div>
}
