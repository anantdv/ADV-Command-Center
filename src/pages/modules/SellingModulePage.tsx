import { useState } from 'react'
import { ErrorState } from '../../components/common/ErrorState'
import { LoadingState } from '../../components/common/LoadingState'
import { ModuleBottomChat } from '../../components/modules/ModuleBottomChat'
import { ModuleHeader } from '../../components/modules/ModuleHeader'
import { SellingDashboard } from '../../components/modules/SellingDashboard'
import { useModuleDashboard } from '../../hooks/api/useModules'

export function SellingModulePage(){
  const dashboard=useModuleDashboard('Selling')
  const [prompt,setPrompt]=useState<string|null>(null)
  const sendPrompt=(value:string)=>setPrompt(`${value} #${Date.now()}`)
  if(dashboard.isLoading)return <LoadingState cards={6}/>
  if(dashboard.isError||!dashboard.data)return <ErrorState retry={()=>void dashboard.refetch()} message="I could not load the Selling module dashboard. Please check ERPNext permissions or module configuration."/>
  return <div className="-m-4 flex h-[calc(100vh-72px)] flex-col bg-[#f8f9fc] sm:-m-6 lg:-m-8">
    <main className="flex-1 space-y-6 overflow-y-auto p-4 pb-44 sm:p-6 lg:p-8">
      <ModuleHeader label="Selling" description="Customers, quotations, sales orders, invoices, and sales analytics." doctypes={dashboard.data.doctypes}/>
      <SellingDashboard dashboard={dashboard.data} onPrompt={sendPrompt}/>
    </main>
    <ModuleBottomChat moduleName="Selling" seedPrompt={prompt}/>
  </div>
}
