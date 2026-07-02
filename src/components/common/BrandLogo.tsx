import advLogo from '../../data/advlogo.png'
import tinniImage from '../../data/Tinni2.png'
import { cn } from '../../utils/cn'

export function BrandLogo({className}:{className?:string}){
  return <span className={cn('relative block shrink-0 overflow-hidden rounded-xl bg-white shadow-sm ring-1 ring-black/5',className)}><img src={advLogo} alt="ADV" className="absolute left-1/2 top-1/2 h-[145%] w-[145%] max-w-none -translate-x-1/2 -translate-y-1/2 object-contain"/></span>
}

export function TinniAvatar({className}:{className?:string}){
  return <span className={cn('block shrink-0 overflow-hidden rounded-full bg-indigo-50 ring-2 ring-white shadow-sm',className)}><img src={tinniImage} alt="Tinni" className="h-full w-full object-cover object-center"/></span>
}
