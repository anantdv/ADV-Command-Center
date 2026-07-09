import { useNavigate } from 'react-router-dom'
import { ErrorState } from '../../components/common/ErrorState'
import { LoadingState } from '../../components/common/LoadingState'
import { ModuleDoctypeNavigation } from '../../components/modules/ModuleDoctypeNavigation'
import { ModuleHeader } from '../../components/modules/ModuleHeader'
import { ModulePinnedCards } from '../../components/modules/ModulePinnedCards'
import { SellingDashboard } from '../../components/modules/SellingDashboard'
import { useModuleDashboard, useModuleDoctypes } from '../../hooks/api/useModules'

export function SellingModulePage(){
  const navigate=useNavigate()
  const dashboard=useModuleDashboard('Selling')
  const doctypes=useModuleDoctypes('Selling')
  const sendPrompt=(value:string,autoRun=true)=>navigate(`/command-center?module=Selling&prompt=${encodeURIComponent(value)}&autoRun=${autoRun?'true':'false'}`)
  const askAi=()=>navigate('/command-center?module=Selling')
  if(dashboard.isLoading)return <LoadingState cards={6}/>
  if(dashboard.isError||!dashboard.data)return <ErrorState retry={()=>void dashboard.refetch()} message="I could not load the Selling module dashboard. Please check ERPNext permissions or module configuration."/>
  return <div className="-m-4 min-h-[calc(100vh-72px)] bg-[#f8f9fc] p-4 sm:-m-6 sm:p-6 lg:-m-8 lg:p-8">
    <main className="space-y-6">
      <ModuleHeader label="Selling" description="Customers, quotations, sales orders, invoices, and sales analytics." doctypes={dashboard.data.doctypes} onAskAi={askAi} onCreateDraft={()=>sendPrompt('create quotation draft',false)}/>
      <SellingDashboard dashboard={dashboard.data} onPrompt={sendPrompt}/>
      <ModulePinnedCards widgets={dashboard.data.pinnedWidgets}/>
      <ModuleDoctypeNavigation moduleName="Selling" doctypes={doctypes.data?.doctypes||[]}/>
    </main>
  </div>
}
