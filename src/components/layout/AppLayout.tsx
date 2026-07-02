import { Outlet } from 'react-router-dom'
import { Sidebar } from './Sidebar'
import { TopHeader } from './TopHeader'

export function AppLayout() { return <div className="flex min-h-screen bg-surface"><Sidebar /><div className="min-w-0 flex-1"><TopHeader /><main className="mx-auto max-w-[1600px] p-4 sm:p-6 lg:p-8"><Outlet /></main></div></div> }
