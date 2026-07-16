export function OcrConfidenceBadge({value}:{value?:number|null}){
  const score=Math.round((value||0)*100)
  const tone=score>=80?'bg-emerald-50 text-emerald-700':score>=50?'bg-amber-50 text-amber-700':'bg-rose-50 text-rose-700'
  return <span className={`rounded-full px-2 py-0.5 text-[10px] font-bold ${tone}`}>{score}%</span>
}
