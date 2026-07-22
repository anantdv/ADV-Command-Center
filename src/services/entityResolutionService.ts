import { apiClient } from './apiClient'
import type { EntitySearchRequest, EntitySearchResponse } from '../types/entityResolution'

export const searchEntity = (request: EntitySearchRequest): Promise<EntitySearchResponse> =>
  apiClient.post('/api/command-center/entity-search', request)
