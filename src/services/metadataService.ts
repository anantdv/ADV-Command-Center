import { apiClient } from './apiClient'
import type { DoctypeIntelligence, FormLayoutIntelligence } from '../types/metadata'

export const getDoctypeIntelligence = (doctype:string, refresh=false):Promise<DoctypeIntelligence> =>
  apiClient.get(`/api/metadata/doctypes/${encodeURIComponent(doctype)}/intelligence${refresh?'?refresh=true':''}`)

export const getDoctypeForm = (doctype:string):Promise<FormLayoutIntelligence> =>
  apiClient.get(`/api/metadata/doctypes/${encodeURIComponent(doctype)}/form`)

