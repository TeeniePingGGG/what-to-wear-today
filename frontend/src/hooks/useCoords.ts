import { useQuery } from '@tanstack/react-query'

export interface Coords {
  latitude: number
  longitude: number
  /** 화면에 보여 줄 위치 이름 */
  name: string
  /** 브라우저 위치 권한으로 얻었는지 (false 면 기본 위치 = 서울) */
  fromDevice: boolean
}

// 위치 권한이 없을 때 쓰는 기본 위치: 서울시청
const FALLBACK: Coords = { latitude: 37.5665, longitude: 126.978, name: '서울', fromDevice: false }

function getPosition(): Promise<Coords> {
  return new Promise((resolve) => {
    if (!('geolocation' in navigator)) return resolve(FALLBACK)
    navigator.geolocation.getCurrentPosition(
      (pos) =>
        resolve({
          latitude: Math.round(pos.coords.latitude * 1e4) / 1e4,
          longitude: Math.round(pos.coords.longitude * 1e4) / 1e4,
          name: '현재 위치',
          fromDevice: true,
        }),
      () => resolve(FALLBACK), // 거부·실패하면 서울
      { timeout: 8000, maximumAge: 10 * 60 * 1000 },
    )
  })
}

/** 현재 위치 (한 번 구하면 화면끼리 공유). 권한을 거부하면 서울로 대신한다. */
export function useCoords() {
  return useQuery({ queryKey: ['coords'], queryFn: getPosition, staleTime: Infinity, gcTime: Infinity })
}
