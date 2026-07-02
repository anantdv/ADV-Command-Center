import { useEffect, useState, type FormEvent } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { ArrowRight, CheckCircle2, Eye, EyeOff, KeyRound, LockKeyhole, ShieldCheck, Sparkles, UserRound } from 'lucide-react'
import { useAuthStore } from '../store/useAuthStore'
import { BrandLogo } from '../components/common/BrandLogo'

export function LoginPage() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const { user, checking, error, login, checkSession } = useAuthStore()
  const navigate = useNavigate()
  const location = useLocation()
  const destination = (location.state as { from?: string } | null)?.from || '/overview'
  useEffect(() => { void checkSession() }, [checkSession])
  useEffect(() => { if (user) navigate(destination, { replace: true }) }, [user, destination, navigate])
  const submit = async (event: FormEvent) => { event.preventDefault(); if (await login(username, password)) navigate(destination, { replace: true }) }

  return <main className="grid min-h-screen bg-white lg:grid-cols-[1.05fr_.95fr]">
    <section className="relative hidden overflow-hidden bg-[radial-gradient(circle_at_20%_10%,#313879_0,#151a34_36%,#090d19_100%)] p-12 text-white lg:flex lg:flex-col">
      <div className="absolute -left-32 bottom-10 size-96 rounded-full bg-indigo-500/20 blur-3xl"/><div className="absolute -right-24 top-10 size-80 rounded-full bg-violet-500/15 blur-3xl"/>
      <div className="relative flex items-center gap-3"><BrandLogo className="size-11"/><div><p className="font-[Manrope] text-sm font-bold">ADV</p><p className="text-[10px] text-slate-400">Command Center</p></div></div>
      <div className="relative my-auto max-w-xl"><span className="inline-flex items-center gap-2 rounded-full border border-indigo-300/20 bg-indigo-400/10 px-3 py-1.5 text-[10px] font-bold uppercase tracking-widest text-indigo-200"><Sparkles size={12}/>Agentic intelligence for ERPNext</span><h1 className="mt-7 font-[Manrope] text-5xl font-bold leading-[1.08] tracking-tight">Your business,<br/><span className="bg-gradient-to-r from-indigo-300 to-violet-300 bg-clip-text text-transparent">ready to answer.</span></h1><p className="mt-6 max-w-lg text-sm leading-7 text-slate-300">Analyze operations, create reports, and safely take action across ERPNext with one permission-aware AI workspace.</p><div className="mt-9 grid gap-3 sm:grid-cols-2">{['Your ERP permissions apply','Write actions need approval','Private session-based access','Complete audit visibility'].map(item=><div key={item} className="flex items-center gap-2.5 text-xs font-semibold text-slate-300"><CheckCircle2 size={15} className="text-emerald-400"/>{item}</div>)}</div></div>
      <div className="relative flex items-center gap-2 text-[10px] text-slate-500"><ShieldCheck size={13} className="text-emerald-400"/>Securely connected to your private ERPNext environment</div>
    </section>
    <section className="flex min-h-screen items-center justify-center bg-[radial-gradient(circle_at_80%_10%,#eef2ff_0,white_38%)] p-5 sm:p-10">
      <div className="w-full max-w-[420px]">
        <div className="mb-9 flex items-center gap-3 lg:hidden"><BrandLogo className="size-11"/><div><p className="font-[Manrope] text-sm font-bold">ADV</p><p className="text-[10px] text-slate-400">Command Center</p></div></div>
        <p className="eyebrow text-indigo-500">Secure workspace access</p><h2 className="mt-3 font-[Manrope] text-3xl font-bold tracking-tight text-slate-950">Welcome back</h2><p className="mt-2 text-sm text-slate-500">Sign in with your existing ERPNext credentials.</p>
        <form onSubmit={submit} className="mt-8 space-y-5">
          <label className="block text-xs font-bold text-slate-700">Email or username<div className="relative mt-2"><UserRound size={17} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400"/><input value={username} onChange={e=>setUsername(e.target.value)} autoComplete="username" required placeholder="you@company.com" className="h-12 w-full rounded-xl border border-slate-200 bg-white pl-11 pr-4 text-sm outline-none transition focus:border-indigo-400 focus:ring-4 focus:ring-indigo-50"/></div></label>
          <label className="block text-xs font-bold text-slate-700">Password<div className="relative mt-2"><KeyRound size={17} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400"/><input value={password} onChange={e=>setPassword(e.target.value)} autoComplete="current-password" required type={showPassword?'text':'password'} placeholder="Enter your ERPNext password" className="h-12 w-full rounded-xl border border-slate-200 bg-white pl-11 pr-12 text-sm outline-none transition focus:border-indigo-400 focus:ring-4 focus:ring-indigo-50"/><button type="button" onClick={()=>setShowPassword(s=>!s)} aria-label={showPassword?'Hide password':'Show password'} className="absolute right-3 top-1/2 -translate-y-1/2 rounded-lg p-1.5 text-slate-400 hover:bg-slate-100">{showPassword?<EyeOff size={16}/>:<Eye size={16}/>}</button></div></label>
          {error&&<div role="alert" className="rounded-xl border border-rose-100 bg-rose-50 px-4 py-3 text-xs font-semibold text-rose-700">{error}</div>}
          <button disabled={checking||!username||!password} className="btn-primary h-12 w-full disabled:cursor-not-allowed disabled:opacity-60">{checking?<><span className="size-4 animate-spin rounded-full border-2 border-white/40 border-t-white"/>Signing in…</>:<>Sign in to Command Center<ArrowRight size={16}/></>}</button>
        </form>
        <div className="mt-6 flex items-start gap-3 rounded-xl bg-slate-50 p-4"><LockKeyhole size={16} className="mt-0.5 shrink-0 text-emerald-600"/><p className="text-[11px] leading-5 text-slate-500"><b className="text-slate-700">Your credentials stay private.</b> They are sent directly to your configured ERPNext server and are never stored by this application.</p></div>
        <p className="mt-7 text-center text-[10px] text-slate-400">ADV Command Center · Enterprise secure access</p>
      </div>
    </section>
  </main>
}
