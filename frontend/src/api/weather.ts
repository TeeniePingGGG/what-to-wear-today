import { useQuery } from '@tanstack/react-query'
import type { Coords } from '../hooks/useCoords'
import type { Weather } from '../types/api'
import { api } from './client'

export function useWeather(coords: Coords | undefined) {
  return useQuery({
    queryKey: ['weather', coords?.latitude, coords?.longitude],
    queryFn: async () =>
      (
        await api.get<Weather>('/weather', {
          params: { lat: coords!.latitude, lon: coords!.longitude, location_name: coords!.name },
        })
      ).data,
    enabled: !!coords,
    staleTime: 10 * 60 * 1000,
  })
}
