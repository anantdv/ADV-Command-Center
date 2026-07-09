import {
  BadgeIndianRupee, Boxes, BriefcaseBusiness, Building2, Factory, Handshake,
  Headphones, IdCard, Landmark, PackageCheck, ReceiptIndianRupee, ShoppingCart, UsersRound,
} from 'lucide-react'
import type { Course, FileItem, Module, Ticket } from '../types'

export const kpis = [
  { label: 'Total Sales', value: '₹42,35,450', change: '+12.5%', trend: 'up' as const, icon: BadgeIndianRupee, accent: 'indigo' },
  { label: 'Total Purchase', value: '₹18,75,000', change: '+4.2%', trend: 'up' as const, icon: ShoppingCart, accent: 'blue' },
  { label: 'Outstanding Receivable', value: '₹8,75,000', change: '-2.4%', trend: 'down' as const, icon: ReceiptIndianRupee, accent: 'amber' },
  { label: 'Outstanding Payable', value: '₹6,45,320', change: '+1.8%', trend: 'up' as const, icon: Building2, accent: 'rose' },
  { label: 'Net Profit', value: '₹12,48,600', change: '+8.7%', trend: 'up' as const, icon: BriefcaseBusiness, accent: 'emerald' },
  { label: 'Stock Value', value: '₹24,16,800', change: '+3.1%', trend: 'up' as const, icon: Boxes, accent: 'violet' },
]

export const salesTrend = [
  { month: 'Jan', sales: 24, purchase: 15 }, { month: 'Feb', sales: 28, purchase: 17 },
  { month: 'Mar', sales: 26, purchase: 18 }, { month: 'Apr', sales: 34, purchase: 19 },
  { month: 'May', sales: 38, purchase: 22 }, { month: 'Jun', sales: 42, purchase: 24 },
]
export const cashFlow = [
  { month: 'Jan', inflow: 26, outflow: 17 }, { month: 'Feb', inflow: 30, outflow: 21 },
  { month: 'Mar', inflow: 29, outflow: 19 }, { month: 'Apr', inflow: 38, outflow: 24 },
  { month: 'May', inflow: 41, outflow: 28 }, { month: 'Jun', inflow: 47, outflow: 30 },
]
export const topCustomers = [
  { name: 'Aster Retail', value: 31, fill: '#6366f1' }, { name: 'Nimbus Labs', value: 24, fill: '#8b5cf6' },
  { name: 'Orbit Works', value: 19, fill: '#22c55e' }, { name: 'Others', value: 26, fill: '#e2e8f0' },
]
export const aging = [
  { range: '0–30', value: 3.8 }, { range: '31–60', value: 2.4 }, { range: '61–90', value: 1.5 }, { range: '90+', value: 0.9 },
]

export const modules: Module[] = [
  { slug: 'accounts', name: 'Accounts', description: 'Ledgers, receivables, payables and financial reporting.', metric: '8', metricLabel: 'Configured DocTypes', icon: Landmark, color: 'indigo' },
  { slug: 'selling', name: 'Selling', description: 'Customers, quotations, sales orders and invoicing.', metric: '₹42.3L', metricLabel: 'Sales this month', icon: ShoppingCart, color: 'blue' },
  { slug: 'buying', name: 'Buying', description: 'Suppliers, purchase orders and procurement cycles.', metric: '84', metricLabel: 'Open orders', icon: PackageCheck, color: 'amber' },
  { slug: 'stock', name: 'Stock', description: 'Items, warehouses, ledgers and reorder intelligence.', metric: '₹24.1L', metricLabel: 'Stock value', icon: Boxes, color: 'emerald' },
  { slug: 'crm', name: 'CRM', description: 'Leads, opportunities and relationship management.', metric: '126', metricLabel: 'Active leads', icon: Handshake, color: 'violet' },
  { slug: 'projects', name: 'Projects', description: 'Project delivery, tasks, timesheets and billing.', metric: '18', metricLabel: 'Active projects', icon: BriefcaseBusiness, color: 'cyan' },
  { slug: 'support', name: 'Support', description: 'Issues, SLAs and customer support operations.', metric: '6', metricLabel: 'Configured DocTypes', icon: Headphones, color: 'sky' },
  { slug: 'hr', name: 'HR', description: 'Employees, attendance, payroll and performance.', metric: '248', metricLabel: 'Employees', icon: IdCard, color: 'rose' },
  { slug: 'assets', name: 'Assets', description: 'Asset records, movement, maintenance and repair.', metric: '6', metricLabel: 'Configured DocTypes', icon: Boxes, color: 'slate' },
  { slug: 'manufacturing', name: 'Manufacturing', description: 'BOMs, work orders and production planning.', metric: '31', metricLabel: 'Open work orders', icon: Factory, color: 'orange' },
]

export const files: FileItem[] = [
  { id: 'file-001', name: 'Monthly Sales Report.xlsx', type: 'Spreadsheet', generatedBy: 'Admin User + AI', module: 'Selling', date: '2026-07-01', permission: 'Team' },
  { id: 'file-002', name: 'Receivable Aging.pdf', type: 'PDF Report', generatedBy: 'Tinni', module: 'Accounting', date: '2026-06-30', permission: 'Company' },
  { id: 'file-003', name: 'Top Customers Chart.png', type: 'Chart', generatedBy: 'Admin User + AI', module: 'Selling', date: '2026-06-28', permission: 'Private' },
  { id: 'file-004', name: 'CEO Overview Dashboard', type: 'Dashboard', generatedBy: 'Tinni', module: 'Cross-module', date: '2026-06-27', permission: 'Company' },
  { id: 'file-005', name: 'Stock Movement Analysis.xlsx', type: 'Spreadsheet', generatedBy: 'Priya Shah + AI', module: 'Stock', date: '2026-06-25', permission: 'Team' },
]

export const courses: Course[] = [
  { id: 'course-001', title: 'ERPNext Selling Basics', module: 'Selling', progress: 72, mandatory: true, duration: '1h 25m' },
  { id: 'course-002', title: 'Purchase Order Approval Process', module: 'Buying', progress: 35, mandatory: true, duration: '45m' },
  { id: 'course-003', title: 'Stock Reconciliation Training', module: 'Stock', progress: 100, mandatory: false, duration: '1h 10m' },
  { id: 'course-004', title: 'Accounts Receivable Management', module: 'Accounting', progress: 58, mandatory: true, duration: '55m' },
  { id: 'course-005', title: 'Project Task Management', module: 'Projects', progress: 0, mandatory: false, duration: '40m' },
]

export const tickets: Ticket[] = [
  { id: 'SUP-2026-0148', subject: 'Unable to submit Sales Invoice', priority: 'High', status: 'In Progress', assignedTo: 'Rahul Mehta', created: '01 Jul 2026' },
  { id: 'SUP-2026-0142', subject: 'Payment Entry not reflecting', priority: 'Medium', status: 'Open', assignedTo: 'AI Triage', created: '30 Jun 2026' },
  { id: 'SUP-2026-0133', subject: 'Stock Ledger mismatch', priority: 'High', status: 'Resolved', assignedTo: 'Sneha Rao', created: '28 Jun 2026' },
  { id: 'SUP-2026-0125', subject: 'Report not loading', priority: 'Low', status: 'Resolved', assignedTo: 'AI Triage', created: '25 Jun 2026' },
]

export const invoices = [
  { id: 'SINV-2026-0418', customer: 'Aster Retail Pvt Ltd', due: '04 Jun 2026', days: 27, amount: '₹1,84,500', risk: 'High' },
  { id: 'SINV-2026-0397', customer: 'Nimbus Labs India', due: '11 Jun 2026', days: 20, amount: '₹1,42,800', risk: 'Medium' },
  { id: 'SINV-2026-0362', customer: 'Orbit Works', due: '18 Jun 2026', days: 13, amount: '₹98,750', risk: 'Low' },
  { id: 'SINV-2026-0341', customer: 'BluePeak Systems', due: '21 Jun 2026', days: 10, amount: '₹76,200', risk: 'Medium' },
]
