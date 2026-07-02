import { modules } from '../../data/mockData'
import type { ModuleDetailResponse, ModuleListResponse, ModuleRecordsResponse, ModuleReportsResponse } from '../../types/module'
import { fullPermission, mockDelay, readOnlyPermission } from './mockUtils'

const moduleRecords: Record<string, string[]> = { accounting:['Trial Balance','General Ledger','Accounts Receivable','Accounts Payable','Journal Entry','Payment Entry'],selling:['Customers','Quotations','Sales Orders','Sales Invoices','Sales Analytics'],stock:['Items','Warehouses','Stock Ledger','Stock Balance','Reorder Report'],buying:['Suppliers','Request for Quotation','Purchase Orders','Purchase Receipts','Purchase Invoices'],crm:['Leads','Opportunities','Prospects','Appointments','Sales Pipeline'],projects:['Projects','Tasks','Timesheets','Activity Cost','Project Billing'],hr:['Employees','Attendance','Leave Applications','Payroll Entry','Performance'],manufacturing:['Bill of Materials','Work Orders','Job Cards','Production Plan','Quality Inspection'] }
const withPermissions = modules.map((module, index) => ({ ...module, permissions: index === 7 ? readOnlyPermission : fullPermission }))
export const mockModuleService = {
  getModules: (): Promise<ModuleListResponse> => mockDelay(withPermissions),
  getModule: async (slug: string): Promise<ModuleDetailResponse> => { const module=withPermissions.find(item=>item.slug===slug); if(!module)throw new Error('Module not found.'); return mockDelay({ module, records: moduleRecords[slug]||[], reports:(moduleRecords[slug]||[]).slice(0,3) }) },
  getModuleRecords: (slug: string): Promise<ModuleRecordsResponse> => mockDelay({ records:(moduleRecords[slug]||[]).map((name,index)=>({name:`${slug.toUpperCase()}-${1000+index}`,title:name})), permissions:withPermissions.find(item=>item.slug===slug)?.permissions||readOnlyPermission }),
  getModuleReports: (slug: string): Promise<ModuleReportsResponse> => mockDelay({ reports:(moduleRecords[slug]||[]).slice(0,3), permissions:fullPermission }),
}
