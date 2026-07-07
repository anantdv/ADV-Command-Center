import type { ExtractedLineItem } from '../../types/documentIntake'

export function ExtractedLineItemsTable({items}:{items:ExtractedLineItem[]}){
 if(!items.length)return <div className="rounded-xl bg-amber-50 p-3 text-xs text-amber-800">Line items were not confidently extracted. Please add them before creating the draft.</div>
 return <div className="overflow-x-auto rounded-xl border border-slate-200"><table className="w-full min-w-[620px] text-left text-xs"><thead className="bg-slate-50 text-[10px] uppercase text-slate-400"><tr>{['Item Code','Description','Qty','UOM','Rate','Amount'].map(label=><th key={label} className="px-3 py-2">{label}</th>)}</tr></thead><tbody>{items.map((item,index)=><tr key={index} className="border-t"><td className="px-3 py-2">{item.item_code||'—'}</td><td className="px-3 py-2">{item.description||item.item_name||'—'}</td><td className="px-3 py-2">{item.qty??'—'}</td><td className="px-3 py-2">{item.uom||'—'}</td><td className="px-3 py-2">{item.rate??'—'}</td><td className="px-3 py-2">{item.amount??'—'}</td></tr>)}</tbody></table></div>
}
