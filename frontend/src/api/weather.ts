import { useQuery } from '@tanstack/react-query'
import type { Coords } from '../hooks/useCoords'
import type { Weather } from '../types/api'
import { api } from './client'
import { fetchOpenMeteo } from './openMeteo'

/** date("YYYY-MM-DD", 오늘·내일)의 날씨. 내일이면 아침 8시 예보가 기준 */
export function useWeather(coords: Coords | undefined, date: string) {
  return useQuery({
    queryKey: ['weather', coords?.latitude, coords?.longitude, date],
    queryFn: async () => {
      const { latitude, longitude, name } = coords!
      const raw = await fetchOpenMeteo(latitude, longitude) // 오늘·내일 2일치. 실패하면 백엔드가 직접 조회
      return (await api.post<Weather>('/weather', { latitude, longitude, location_name: name, raw, date })).data
    },
    enabled: !!coords,
    staleTime: 10 * 60 * 1000,
  })
}
