import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import type { FeedbackIn, OutfitDetail } from '../types/api'
import { api } from './client'

const key = (id: number) => ['outfit', id]

/** 코디 상세 (옷, 그날의 조건, 가이드, 피드백) */
export function useOutfit(id: number) {
  return useQuery({
    queryKey: key(id),
    queryFn: async () => (await api.get<OutfitDetail>(`/outfits/${id}`)).data,
    enabled: Number.isFinite(id),
  })
}

/** AI 스타일리스트 가이드 만들기 (regenerate: 이미 있어도 새로) */
export function useGenerateGuide(id: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (regenerate: boolean = false) =>
      (await api.post<OutfitDetail>(`/outfits/${id}/guide`, null, { params: { regenerate } })).data,
    onSuccess: (data) => qc.setQueryData(key(id), data),
  })
}

export function useSaveFeedback(id: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (body: FeedbackIn) => (await api.put<OutfitDetail>(`/outfits/${id}/feedback`, body)).data,
    onSuccess: (data) => {
      qc.setQueryData(key(id), data)
      qc.invalidateQueries({ queryKey: ['clothes'] }) // 세탁 중 상태가 바뀌었을 수 있음
      qc.invalidateQueries({ queryKey: ['recommendation'] })
    },
  })
}

export function useDeleteFeedback(id: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async () => {
      await api.delete(`/outfits/${id}/feedback`)
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: key(id) })
      qc.invalidateQueries({ queryKey: ['recommendation'] })
    },
  })
}
