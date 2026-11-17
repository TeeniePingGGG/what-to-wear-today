import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import type { Recommendation, RecommendRequest } from '../types/api'
import { api } from './client'
import { fetchOpenMeteo } from './openMeteo'

const recKey = (date: string) => ['recommendation', date]

/** 그날(date: "YYYY-MM-DD", 오늘·내일) 받은 가장 최근 추천 (없으면 null) */
export function useRecommendation(date: string) {
  return useQuery({
    queryKey: recKey(date),
    queryFn: async () => (await api.get<Recommendation | null>('/recommendations/today', { params: { date } })).data,
  })
}

/** 날씨 + 일정 + 상황으로 새 코디 추천 (target_date 로 오늘·내일 선택) */
export function useCreateRecommendation() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (body: RecommendRequest) => {
      const raw_weather = await fetchOpenMeteo(body.latitude, body.longitude)
      return (await api.post<Recommendation>('/recommendations', { ...body, raw_weather })).data
    },
    onSuccess: (rec) => qc.setQueryData(recKey(rec.target_date), rec),
  })
}

/** '이걸로 입을게요' */
export function useSelectOutfit() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (outfitId: number) => (await api.post<Recommendation>(`/outfits/${outfitId}/select`)).data,
    onSuccess: (rec) => {
      qc.setQueryData(recKey(rec.target_date), rec)
      qc.invalidateQueries({ queryKey: ['clothes'] }) // 착용 횟수 갱신
    },
  })
}
