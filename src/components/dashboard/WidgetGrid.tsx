import type { DashboardWidgetData } from '../../types/dashboard'
import { DashboardWidget } from './DashboardWidget'
export function WidgetGrid({widgets,onRefresh,onDelete,onEdit,busyId}:{widgets:DashboardWidgetData[];onRefresh?:(id:string)=>void;onDelete?:(id:string)=>void;onEdit?:(widget:DashboardWidgetData)=>void;busyId?:string}){
 return <div className="grid gap-5 lg:grid-cols-2">{widgets.map(widget=><DashboardWidget key={widget.widget_id} widget={widget} busy={busyId===widget.widget_id} onRefresh={onRefresh?()=>onRefresh(widget.widget_id):undefined} onDelete={onDelete?()=>onDelete(widget.widget_id):undefined} onEdit={onEdit?()=>onEdit(widget):undefined}/>)}</div>
}
