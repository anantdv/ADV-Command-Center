import { BadgeIndianRupee, Boxes, BriefcaseBusiness, Factory, Handshake, PackageCheck, ShoppingCart, UsersRound, type LucideIcon } from 'lucide-react'
import { env } from '../config/env'
import type { Module, ModuleDashboard, ModuleDetailResponse, ModuleDoctypeNavigation, ModuleDoctypeRecords, ModuleListResponse, ModuleRecordsResponse, ModuleReportsResponse } from '../types/module'
import { apiClient } from './apiClient'
import { mockModuleService } from './mock/mockModuleService'
type ModuleDto=Omit<Module,'icon'>;type DetailDto=Omit<ModuleDetailResponse,'module'>&{module:ModuleDto}
const icons:Record<string,LucideIcon>={accounting:BadgeIndianRupee,accounts:BadgeIndianRupee,selling:ShoppingCart,buying:PackageCheck,stock:Boxes,crm:Handshake,projects:BriefcaseBusiness,hr:UsersRound,manufacturing:Factory}
const hydrate=(module:ModuleDto):Module=>({...module,icon:icons[module.slug]||Boxes})
export async function getModules():Promise<ModuleListResponse>{if(env.useMockApi)return mockModuleService.getModules();return(await apiClient.get<ModuleDto[]>('/api/modules')).map(hydrate)}
export async function getModule(name:string):Promise<ModuleDetailResponse>{if(env.useMockApi)return mockModuleService.getModule(name);const result=await apiClient.get<DetailDto>(`/api/modules/${encodeURIComponent(name)}`);return{...result,module:hydrate(result.module)}}
export const getModuleDashboard=(name:string):Promise<ModuleDashboard>=>apiClient.get(`/api/modules/${encodeURIComponent(name)}/dashboard`)
export const getModuleDoctypes=(name:string):Promise<ModuleDoctypeNavigation>=>apiClient.get(`/api/modules/${encodeURIComponent(name)}/doctypes`)
export const getModuleDoctypeRecords=({moduleName,doctype,page=1,pageSize=20,search}:{moduleName:string;doctype:string;page?:number;pageSize?:number;search?:string}):Promise<ModuleDoctypeRecords>=>{const params=new URLSearchParams({page:String(page),page_size:String(pageSize)});if(search)params.set('search',search);return apiClient.get(`/api/modules/${encodeURIComponent(moduleName)}/doctype/${encodeURIComponent(doctype)}/records?${params}`)}
export const getModuleRecords=(name:string):Promise<ModuleRecordsResponse>=>env.useMockApi?mockModuleService.getModuleRecords(name):apiClient.get(`/api/modules/${encodeURIComponent(name)}/records`)
export const getModuleReports=(name:string):Promise<ModuleReportsResponse>=>env.useMockApi?mockModuleService.getModuleReports(name):apiClient.get(`/api/modules/${encodeURIComponent(name)}/reports`)
