import { lazy, Suspense, type ReactNode } from 'react'
import { createBrowserRouter, Navigate } from 'react-router-dom'
import { AppLayout } from '../components/layout/AppLayout'
import { AuthGuard } from '../components/auth/AuthGuard'

const OverviewPage = lazy(() => import('../pages/OverviewPage').then(m => ({ default: m.OverviewPage })))
const CommandCenterPage = lazy(() => import('../pages/CommandCenterPage').then(m => ({ default: m.CommandCenterPage })))
const ModulesPage = lazy(() => import('../pages/ModulesPage').then(m => ({ default: m.ModulesPage })))
const ModuleDetailPage = lazy(() => import('../pages/ModuleDetailPage').then(m => ({ default: m.ModuleDetailPage })))
const SellingModulePage = lazy(() => import('../pages/modules/SellingModulePage').then(m => ({ default: m.SellingModulePage })))
const ModuleWorkspacePage = lazy(() => import('../pages/modules/ModuleWorkspacePage').then(m => ({ default: m.ModuleWorkspacePage })))
const LibraryPage = lazy(() => import('../pages/LibraryPage').then(m => ({ default: m.LibraryPage })))
const TrainingPage = lazy(() => import('../pages/TrainingPage').then(m => ({ default: m.TrainingPage })))
const SupportPage = lazy(() => import('../pages/SupportPage').then(m => ({ default: m.SupportPage })))
const SettingsPage = lazy(() => import('../pages/SettingsPage').then(m => ({ default: m.SettingsPage })))
const CommunicationCenterPage = lazy(() => import('../features/communications/pages/CommunicationCenterPage').then(m => ({ default: m.CommunicationCenterPage })))
const LoginPage = lazy(() => import('../pages/LoginPage').then(m => ({ default: m.LoginPage })))
const page = (content: ReactNode) => <Suspense fallback={<div className="grid min-h-[50vh] place-items-center"><div className="size-8 animate-spin rounded-full border-2 border-slate-200 border-t-indigo-600" /></div>}>{content}</Suspense>

export const router=createBrowserRouter([
  { path:'/login', element:page(<LoginPage/>) },
  {path:'/',element:<AuthGuard><AppLayout/></AuthGuard>,children:[
  {index:true,element:<Navigate to="/overview" replace/>},
  {path:'overview',element:page(<OverviewPage/>)},{path:'command-center',element:page(<CommandCenterPage/>)},
  {path:'communications',element:page(<CommunicationCenterPage/>)},
  {path:'modules',element:page(<ModulesPage/>)},{path:'modules/selling',element:page(<SellingModulePage/>)},{path:'modules/:moduleName',element:page(<ModuleWorkspacePage/>)},{path:'modules/:moduleId/legacy',element:page(<ModuleDetailPage/>)},
  {path:'library',element:page(<LibraryPage/>)},{path:'library/:category',element:page(<LibraryPage/>)},
  {path:'training',element:page(<TrainingPage/>)},{path:'training/:section',element:page(<TrainingPage/>)},
  {path:'support',element:page(<SupportPage/>)},{path:'support/:section',element:page(<SupportPage/>)},
  {path:'settings',element:page(<SettingsPage/>)},{path:'*',element:<Navigate to="/overview" replace/>},
]}])
