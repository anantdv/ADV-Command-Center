import { Sparkles } from 'lucide-react'
import { PageHeader } from '../components/common/PageHeader'
import { ModuleCard } from '../components/modules/ModuleCard'
import { LoadingState } from '../components/common/LoadingState'
import { ErrorState } from '../components/common/ErrorState'
import { useModules } from '../hooks/api/useModules'
export function ModulesPage(){const query=useModules();if(query.isLoading)return <LoadingState/>;if(query.isError||!query.data)return <ErrorState retry={()=>void query.refetch()}/>;return <><PageHeader eyebrow="ERP workspace" title="Business Modules" description="Explore every ERPNext area or let AI work across modules with your existing permissions." actions={<button className="btn-primary"><Sparkles size={16}/>Ask across modules</button>}/><div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">{query.data.map(m=><ModuleCard key={m.slug} module={m}/>)}</div></>}
