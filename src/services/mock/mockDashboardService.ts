import type { CreateDashboardWidgetRequest, DashboardOverviewResponse, DashboardWidgetData, DashboardWidgetLayout, PinChatResultRequest, UpdateDashboardWidgetRequest } from '../../types/dashboard'
import { mockDelay } from './mockUtils'
const source={source_type:'doctype' as const,doctype:'Customer',source_name:'Customer',aggregate_function:'count' as const}
let widgets:DashboardWidgetData[]=[]
const kpi:DashboardWidgetData={widget_id:'default_0',title:'Total Customers',widget_type:'kpi',source,layout:{x:0,y:0,w:4,h:3},data:{value:128,format:'number',subtitle:'Customers you can access'},permission:{allowed:true},last_refreshed_at:new Date().toISOString(),label:'Total Customers',value:128}
const build=(request:CreateDashboardWidgetRequest,id=`widget_${Date.now()}`):DashboardWidgetData=>({widget_id:id,title:request.title,widget_type:request.widget_type,source:request.source,chart_config:request.chart_config,layout:{x:0,y:0,w:4,h:3,...request.layout},data:request.widget_type==='table'?{columns:[{key:'name',label:'Name'}],rows:[{name:'CUST-0001'}]}:{value:1},permission:{allowed:true},last_refreshed_at:new Date().toISOString(),refresh_interval_seconds:request.refresh_interval_seconds||300,visibility:request.visibility||'private'})
export const mockDashboardService={
 getDashboardOverview:():Promise<DashboardOverviewResponse>=>mockDelay({kpis:[kpi],widgets,insights:['Every widget refresh re-checks your ERPNext permissions.']}),
 getDashboardWidgets:()=>mockDelay(widgets),
 createDashboardWidget:(request:CreateDashboardWidgetRequest)=>{const widget=build(request);widgets=[...widgets,widget];return mockDelay(widget)},
 refreshDashboardWidget:(id:string)=>mockDelay({...widgets.find(w=>w.widget_id===id)!,last_refreshed_at:new Date().toISOString()}),
 updateDashboardWidget:(id:string,request:UpdateDashboardWidgetRequest)=>{widgets=widgets.map(w=>w.widget_id===id?{...w,...request,layout:request.layout?{...w.layout,...request.layout}:w.layout}:w);return mockDelay(widgets.find(w=>w.widget_id===id)!)},
 deleteDashboardWidget:(id:string)=>{widgets=widgets.filter(w=>w.widget_id!==id);return mockDelay(true)},
 reorderDashboardWidgets:(_layouts:Array<{widget_id:string;layout:DashboardWidgetLayout}>)=>mockDelay(true),
 pinChatResultToDashboard:(request:PinChatResultRequest)=>{const widget=build({...request});widgets=[...widgets,widget];return mockDelay({widget_id:widget.widget_id,title:widget.title,message:'Pinned to Overview successfully.'})},
}
