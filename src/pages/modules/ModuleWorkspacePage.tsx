import { useParams } from 'react-router-dom'
import { useState } from 'react'
import { ErrorState } from '../../components/common/ErrorState'
import { LoadingState } from '../../components/common/LoadingState'
import { ModuleBottomChat } from '../../components/modules/ModuleBottomChat'
import { ModuleHeader } from '../../components/modules/ModuleHeader'
import { ModuleKpiCard } from '../../components/modules/ModuleKpiCard'
import { ModuleQuickActions } from '../../components/modules/ModuleQuickActions'
import { useModuleDashboard } from '../../hooks/api/useModules'

export function ModuleWorkspacePage(){
  const {moduleName='Selling'}=useParams()
  const dashboard=useModuleDashboard(moduleName)
  const [prompt,setPrompt]=useState<string|null>(null)
  const sendPrompt=(value:string)=>setPrompt(`${value} #${Date.now()}`)
  if(dashboard.isLoading)return <LoadingState cards={5}/>
  if(dashboard.isError||!dashboard.data)return <ErrorState retry={()=>void dashboard.refetch()} message={`I could not load the ${moduleName} module dashboard.`}/>
  return <div className="-m-4 flex h-[calc(100vh-72px)] flex-col bg-[#f8f9fc] sm:-m-6 lg:-m-8">
    <main className="flex-1 space-y-6 overflow-y-auto p-4 pb-44 sm:p-6 lg:p-8">
      <ModuleHeader label={dashboard.data.label} doctypes={dashboard.data.doctypes}/>
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">{dashboard.data.kpis.map(kpi=><ModuleKpiCard key={kpi.id} kpi={kpi} onClick={sendPrompt}/>)}</div>
      <div className="grid gap-5 xl:grid-cols-3">
        <section className="card p-5 xl:col-span-2"><h3 className="text-sm font-bold text-slate-900">Permitted DocTypes</h3><div className="mt-4 flex flex-wrap gap-2">{dashboard.data.doctypes.map(doctype=><span key={doctype} className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-semibold text-slate-600">{doctype}</span>)}</div></section>
        <ModuleQuickActions actions={dashboard.data.quickActions} onPrompt={sendPrompt}/>
      </div>
    </main>
    <ModuleBottomChat moduleName={dashboard.data.label} seedPrompt={prompt}/>
  </div>
}
