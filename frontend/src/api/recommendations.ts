import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import type { Recommendation, RecommendRequest } from '../types/api'
import { api } from './client'

const TODAY_KEY = ['recommendation', 'today']

/** 오늘 받은 가장 최근 추천 (없으면 null) */
export function useTodayRecommendation() {
  return useQuery({
    queryKey: TODAY_KEY,
    queryFn: async () => (await api.get<Recommendation | null>('/recommendations/today')).data,
  })
}

/** 날씨 + 일정 + 상황으로 새 코디 추천 */
export function useCreateRecommendation() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (body: RecommendRequest) => (await api.post<Recommendation>('/recommendations', body)).data,
    onSuccess: (rec) => qc.setQueryData(TODAY_KEY, rec),
  })
}

/** '이걸로 입을게요' */
export function useSelectOutfit() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (outfitId: number) => (await api.post<Recommendation>(`/outfits/${outfitId}/select`)).data,
    onSuccess: (rec) => {
      qc.setQueryData(TODAY_KEY, rec)
      qc.invalidateQueries({ queryKey: ['clothes'] }) // 착용 횟수 갱신
    },
  })
}
