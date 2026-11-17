import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import type { Schedule, ScheduleCreate } from '../types/api'
import { api } from './client'

/** 그날(date: "YYYY-MM-DD") 일정 */
export function useSchedules(date: string) {
  return useQuery({
    queryKey: ['schedules', date],
    queryFn: async () => (await api.get<Schedule[]>('/schedules', { params: { date } })).data,
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
