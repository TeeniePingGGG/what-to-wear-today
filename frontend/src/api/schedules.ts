import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import type { Schedule, ScheduleCreate } from '../types/api'
import { api } from './client'

/** 오늘 일정 */
export function useSchedules() {
  return useQuery({
    queryKey: ['schedules', 'today'],
    queryFn: async () => (await api.get<Schedule[]>('/schedules')).data,
  })
}

export function useAddSchedule() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (body: ScheduleCreate) => (await api.post<Schedule>('/schedules', body)).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['schedules'] }),
  })
}

export function useDeleteSchedule() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (id: number) => {
      await api.delete(`/schedules/${id}`)
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['schedules'] }),
  })
}
