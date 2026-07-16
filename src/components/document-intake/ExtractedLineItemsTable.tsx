import type { ExtractedLineItem } from '../../types/documentIntake'
import { useState } from 'react'
import { searchLink } from '../../services/erpnextService'

export function ExtractedLineItemsTable({items,onChange}:{items:ExtractedLineItem[];onChange?:(items:ExtractedLineItem[])=>void}){
 const [searching,setSearching]=useState<number|null>(null)
 const update=(index:number,key:keyof ExtractedLineItem,value:string)=>{const next=[...items];const numeric=['qty','rate','amount'].includes(key);next[index]={...next[index],[key]:numeric?(value===''?null:Number(value)):value};if(key==='qty'||key==='rate'){const qty=Number(next[index].qty||0);const rate=Number(next[index].rate||0);if(qty&&rate)next[index].amount=Number((qty*rate).toFixed(2))}onChange?.(next)}
 const searchItem=async(index:number)=>{setSearching(index);try{const item=items[index];const results=await searchLink('Item',String(item.description||item.item_name||item.item_code||''));if(results[0])update(index,'item_code',results[0].name)}finally{setSearching(null)}}
 const add=()=>onChange?.([...items,{item_code:'',description:'',qty:1,uom:'Nos',rate:0,amount:0}])
 const remove=(index:number)=>onChange?.(items.filter((_,i)=>i!==index))
 return <div>
  {!items.length&&<div className="mb-3 rounded-xl bg-amber-50 p-3 text-xs text-amber-800">Line items were not confidently extracted. Please add them before creating the draft.</div>}
  <div className="overflow-x-auto rounded-xl border border-slate-200"><table className="w-full min-w-[760px] text-left text-xs"><thead className="bg-slate-50 text-[10px] uppercase text-slate-400"><tr>{['Item Code','Description','Qty','UOM','Rate','Amount',''].map(label=><th key={label} className="px-3 py-2">{label}</th>)}</tr></thead><tbody>{items.map((item,index)=><tr key={index} className="border-t">
   <td className="px-3 py-2"><div className="flex gap-1"><input value={item.item_code||''} onChange={e=>update(index,'item_code',e.target.value)} className="h-8 w-28 rounded border px-2"/><button type="button" onClick={()=>void searchItem(index)} className="rounded border px-2 text-[10px]">{searching===index?'…':'Find'}</button></div>{(item.candidates?.length||0)>0&&<div className="mt-1 space-y-1">{item.candidates?.slice(0,2).map((candidate,idx)=><button key={idx} type="button" onClick={()=>update(index,'item_code',String(candidate.name||candidate.item_code||''))} className="block rounded bg-indigo-50 px-2 py-1 text-left text-[10px] text-indigo-700">{String(candidate.item_name||candidate.name||candidate.item_code||'')} · {Math.round(Number(candidate.score||0)*100)}%</button>)}</div>}</td>
   <td className="px-3 py-2"><input value={item.description||item.item_name||''} onChange={e=>update(index,'description',e.target.value)} className="h-8 w-52 rounded border px-2"/>{item.warning&&<p className="mt-1 text-[10px] text-amber-700">{item.warning}</p>}</td>
   <td className="px-3 py-2"><input value={item.qty??''} onChange={e=>update(index,'qty',e.target.value)} className="h-8 w-20 rounded border px-2"/></td>
   <td className="px-3 py-2"><input value={item.uom||''} onChange={e=>update(index,'uom',e.target.value)} className="h-8 w-20 rounded border px-2"/></td>
   <td className="px-3 py-2"><input value={item.rate??''} onChange={e=>update(index,'rate',e.target.value)} className="h-8 w-24 rounded border px-2"/></td>
   <td className="px-3 py-2"><input value={item.amount??''} onChange={e=>update(index,'amount',e.target.value)} className="h-8 w-24 rounded border px-2"/></td>
   <td className="px-3 py-2"><button type="button" onClick={()=>remove(index)} className="text-rose-600">Remove</button></td>
  </tr>)}</tbody></table></div>
  <button type="button" onClick={add} className="btn-secondary mt-3 h-9 px-3 text-xs">Add Item Manually</button>
 </div>
}
