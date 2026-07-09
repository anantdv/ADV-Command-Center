import { useQuery } from '@tanstack/react-query'
import { getModule, getModuleDashboard, getModuleRecords, getModuleReports, getModules } from '../../services/moduleService'
export const moduleKeys={all:['modules'] as const,detail:(name:string)=>['modules',name] as const,dashboard:(name:string)=>['modules',name,'dashboard'] as const,records:(name:string)=>['modules',name,'records'] as const,reports:(name:string)=>['modules',name,'reports'] as const}
export const useModules=()=>useQuery({queryKey:moduleKeys.all,queryFn:getModules})
export const useModule=(name:string)=>useQuery({queryKey:moduleKeys.detail(name),queryFn:()=>getModule(name),enabled:Boolean(name)})
export const useModuleDashboard=(name:string)=>useQuery({queryKey:moduleKeys.dashboard(name),queryFn:()=>getModuleDashboard(name),enabled:Boolean(name)})
export const useModuleRecords=(name:string)=>useQuery({queryKey:moduleKeys.records(name),queryFn:()=>getModuleRecords(name),enabled:Boolean(name)})
export const useModuleReports=(name:string)=>useQuery({queryKey:moduleKeys.reports(name),queryFn:()=>getModuleReports(name),enabled:Boolean(name)})
