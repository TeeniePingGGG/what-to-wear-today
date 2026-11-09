import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import type { AnalyzeResponse, Category, Clothing, ClothingCreate, ClothingStatus, ReanalyzeResponse } from '../types/api'
import { api } from './client'

export function useClothes(params: { category?: Category; status?: ClothingStatus } = {}) {
  return useQuery({
    queryKey: ['clothes', params],
    queryFn: async () => (await api.get<Clothing[]>('/clothes', { params })).data,
  })
}

/** 사진 → 배경 제거 + AI 분석 (아직 옷장에 저장하지 않음) */
export function useAnalyzeClothing() {
  return useMutation({
    mutationFn: async (image: File) => {
      const form = new FormData()
      form.append('image', image)
      return (await api.post<AnalyzeResponse>('/clothes/analyze', form)).data
    },
  })
}

/** 이미 올린 사진으로 AI 분석만 다시 */
export function useReanalyzeClothing() {
  return useMutation({
    mutationFn: async (imageUrl: string) =>
      (await api.post<ReanalyzeResponse>('/clothes/reanalyze', { image_url: imageUrl })).data,
  })
}

/** 검수한 값으로 옷장에 저장 */
export function useCreateClothing() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (body: ClothingCreate) => (await api.post<Clothing>('/clothes', body)).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['clothes'] }),
  })
}

export function useUpdateClothing() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async ({ id, ...body }: Partial<Clothing> & { id: number }) =>
      (await api.patch<Clothing>(`/clothes/${id}`, body)).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['clothes'] }),
  })
}

export function useDeleteClothing() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (id: number) => {
      await api.delete(`/clothes/${id}`)
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['clothes'] }),
  })
}
