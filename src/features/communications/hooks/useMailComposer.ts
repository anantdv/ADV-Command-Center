import {useState} from 'react'
import type {ComposerData} from '../types/communication.types'
const empty:ComposerData={to:[],cc:[],bcc:[],subject:'',content:'',attachments:[]}
export function useMailComposer(){const[data,setData]=useState<ComposerData>(empty);return{data,setData,reset:()=>setData(empty)}}
