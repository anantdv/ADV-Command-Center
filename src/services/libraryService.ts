import { env } from '../config/env'
import type { CreateLibraryFileRequest, FileItem, LibraryFilesResponse } from '../types/library'
import { apiClient } from './apiClient'
import { mockLibraryService } from './mock/mockLibraryService'
export const getLibraryFiles=(category?:string):Promise<LibraryFilesResponse>=>env.useMockApi?mockLibraryService.getFiles(category):apiClient.get(`/api/library/files${category?`?category=${encodeURIComponent(category)}`:''}`)
export const createLibraryFile=(request:CreateLibraryFileRequest):Promise<FileItem>=>env.useMockApi?mockLibraryService.createFile(request):apiClient.post('/api/library/files',request)
export const deleteLibraryFile=(id:string):Promise<{success:boolean}>=>env.useMockApi?mockLibraryService.deleteFile(id):apiClient.delete(`/api/library/files/${encodeURIComponent(id)}`)
