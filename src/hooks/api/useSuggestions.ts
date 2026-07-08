import { useMutation } from '@tanstack/react-query'
import { executeSuggestion, generateSuggestions } from '../../services/suggestionService'

export const useGenerateSuggestions=()=>useMutation({mutationFn:generateSuggestions})
export const useExecuteSuggestion=()=>useMutation({mutationFn:executeSuggestion})
