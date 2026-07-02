import { files } from '../../data/mockData'
import type { CreateLibraryFileRequest, FileItem } from '../../types/library'
import { fullPermission, mockDelay, readOnlyPermission } from './mockUtils'

let libraryFiles: FileItem[] = files.map((file,index)=>({ ...file, permissions:index===2?readOnlyPermission:fullPermission }))
export const mockLibraryService = {
  getFiles: (category?: string) => mockDelay(category ? libraryFiles.filter(file => ({spreadsheets:'Spreadsheet',pdf:'PDF Report',charts:'Chart',dashboards:'Dashboard'} as Record<string,string>)[category]===file.type) : libraryFiles),
  createFile: (request: CreateLibraryFileRequest) => { const file:FileItem={...request,id:`file-${Date.now()}`,generatedBy:'Admin User + AI',date:new Date().toISOString(),permission:'Private',permissions:fullPermission};libraryFiles=[file,...libraryFiles];return mockDelay(file) },
  deleteFile: (id: string) => { libraryFiles=libraryFiles.filter(file=>file.id!==id); return mockDelay({success:true}) },
}
