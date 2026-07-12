import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { AlertTriangle, Boxes, Building2, PackageSearch, ReceiptIndianRupee, RefreshCw, Sparkles, Users } from 'lucide-react'
import { PageHeader } from '../components/common/PageHeader'
import { KpiCard } from '../components/common/KpiCard'
import { LoadingState } from '../components/common/LoadingState'
import { ErrorState } from '../components/common/ErrorState'
import { EmptyState } from '../components/common/EmptyState'
import { WidgetGrid } from '../components/dashboard/WidgetGrid'
import { WidgetConfigDialog } from '../components/dashboard/WidgetConfigDialog'
import { useDashboardOverview, useDeleteDashboardWidget, useRefreshDashboardWidget, useUpdateDashboardWidget } from '../hooks/api/useDashboard'
import type { DashboardWidgetData, UpdateDashboardWidgetRequest } from '../types/dashboard'
import { useAuthStore } from '../store/useAuthStore'
import { formatCurrency } from '../utils/formatters'

const icons:Record<string,typeof Users>={'Total Customers':Users,'Total Suppliers':Building2,'Total Items':Boxes,'Open Sales Orders':ReceiptIndianRupee,'Open Purchase Orders':ReceiptIndianRupee,'Overdue Sales Invoices':AlertTriangle,'Outstanding Receivable':ReceiptIndianRupee,'Outstanding Payable':Building2}
export function OverviewPage(){
 const navigate=useNavigate();const user=useAuthStore(state=>state.user);const currency=user?.companyCurrency||'INR';const overview=useDashboardOverview();const refresh=useRefreshDashboardWidget();const remove=useDeleteDashboardWidget();const update=useUpdateDashboardWidget();const [editing,setEditing]=useState<DashboardWidgetData|null>(null)
 if(overview.isLoading)return <LoadingState cards={8}/>
 if(overview.isError||!overview.data)return <ErrorState retry={()=>void overview.refetch()}/>
 const formatValue=(widget:DashboardWidgetData)=>{const data=!Array.isArray(widget.data)?widget.data:null;const value=data?.value??widget.value??0;return data?.format==='currency'?formatCurrency(Number(value),currency):new Intl.NumberFormat('en-IN').format(Number(value))}
 const refreshWidget=(id:string)=>id.startsWith('default_')?void overview.refetch():refresh.mutate(id)
 const save=(request:UpdateDashboardWidgetRequest)=>{if(!editing)return;update.mutate({id:editing.widget_id,request},{onSuccess:()=>setEditing(null)})}
 return <><PageHeader eyebrow="Live ERPNext overview" title={`${getGreeting()}, ${getFirstName(user)}`} description="ERPNext KPIs and widgets refreshed from your data." actions={<div className="flex gap-2"><button onClick={()=>void overview.refetch()} className="btn-secondary"><RefreshCw size={15}/>Refresh all</button><button onClick={()=>navigate('/command-center')} className="btn-primary"><Sparkles size={16}/>Ask Tinni</button></div>}/>
 <div className="grid grid-cols-2 gap-3 lg:grid-cols-4 2xl:grid-cols-8">{overview.data.kpis.map(widget=><KpiCard key={widget.widget_id} label={widget.title} value={formatValue(widget)} icon={icons[widget.title]||PackageSearch} accent={widget.error?'amber':widget.accent||'indigo'}/>)}</div>
 <div className="mt-7 mb-4 flex items-center justify-between"><div><h2 className="font-[Manrope] text-lg font-bold">Dashboard widgets</h2><p className="mt-1 text-xs text-slate-400">Pinned results and ERPNext defaults</p></div></div>
 {overview.data.widgets.length?<WidgetGrid widgets={overview.data.widgets} busyId={refresh.variables} onRefresh={refreshWidget} onDelete={id=>!id.startsWith('default_')&&remove.mutate(id)} onEdit={widget=>!widget.widget_id.startsWith('default_')&&setEditing(widget)}/>:<EmptyState title="No dashboard widgets" description="Ask Tinni for ERPNext data, then pin the result to your Overview." action={<button onClick={()=>navigate('/command-center')} className="btn-primary"><Sparkles size={15}/>Open Command Center</button>}/>} 
 {overview.data.insights.length>0&&<section className="card mt-6 p-5"><h2 className="flex items-center gap-2 text-sm font-bold"><Sparkles size={15} className="text-indigo-600"/>Dashboard notes</h2><div className="mt-3 grid gap-3 md:grid-cols-2">{overview.data.insights.map(item=><p key={item} className="rounded-xl bg-slate-50 p-3 text-xs leading-5 text-slate-500">{item}</p>)}</div></section>}
 {editing&&<WidgetConfigDialog widget={editing} onClose={()=>setEditing(null)} onSave={save} saving={update.isPending}/>}</>
}

function getGreeting(date = new Date()) {
 const hour = date.getHours()
 if(hour < 12) return 'Good morning'
 if(hour < 17) return 'Good afternoon'
 return 'Good evening'
}

function getFirstName(user: ReturnType<typeof useAuthStore.getState>['user']) {
 const name = user?.firstName || user?.fullName || user?.user?.split('@')[0]
 return name?.split(/\s+/)[0] || 'there'
}
