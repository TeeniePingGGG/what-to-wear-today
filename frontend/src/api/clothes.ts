import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import type { Category, Clothing, ClothingCreate, ClothingStatus, MultiAnalyzeResponse, ReanalyzeResponse } from '../types/api'
import { api } from './client'

export function useClothes(params: { category?: Category; status?: ClothingStatus } = {}) {
  return useQuery({
    queryKey: ['clothes', params],
    queryFn: async () => (await api.get<Clothing[]>('/clothes', { params })).data,
  })
}

/** 사진 → AI가 옷을 전부 찾아 한 벌씩 잘라 배경 제거 + 분석 (아직 옷장에 저장하지 않음) */
export function useAnalyzeClothing() {
  return useMutation({
    mutationFn: async (image: File) => {
      const form = new FormData()
      form.append('image', image)
      return (await api.post<MultiAnalyzeResponse>('/clothes/analyze', form)).data
    },
  })
}

/** 이미 올린 원본 사진으로 옷 찾기를 다시 (AI 실패 시) */
export function useRedetectClothing() {
  return useMutation({
    mutationFn: async (originalImageUrl: string) =>
      (await api.post<MultiAnalyzeResponse>('/clothes/redetect', { original_image_url: originalImageUrl })).data,
  })
}

/** 이미 올린 사진으로 AI 분석만 다시 */
export function useReanalyzeClothing() {
  return useMutation({
    mutationFn: async (imageUrl: string) =>
      (await api.post<ReanalyzeResponse>('/clothes/reanalyze', { image_url: imageUrl })).data,
  })
}

/** 여러 벌을 한 번에 저장 */
export function useCreateClothesBulk() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (items: ClothingCreate[]) => (await api.post<Clothing[]>('/clothes/bulk', { items })).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['clothes'] }),
  })
}

/** 검수한 값으로 옷장에 저장 (한 벌) */
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
