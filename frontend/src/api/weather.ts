import { useQuery } from '@tanstack/react-query'
import type { Coords } from '../hooks/useCoords'
import type { Weather } from '../types/api'
import { api } from './client'
import { fetchOpenMeteo } from './openMeteo'

export function useWeather(coords: Coords | undefined) {
  return useQuery({
    queryKey: ['weather', coords?.latitude, coords?.longitude],
    queryFn: async () => {
      const { latitude, longitude, name } = coords!
      const raw = await fetchOpenMeteo(latitude, longitude) // 실패하면 백엔드가 직접 조회
      return (await api.post<Weather>('/weather', { latitude, longitude, location_name: name, raw })).data
    },
    enabled: !!coords,
    staleTime: 10 * 60 * 1000,
  })
}
