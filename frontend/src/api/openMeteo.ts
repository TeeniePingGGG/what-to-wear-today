/**
 * 브라우저에서 Open-Meteo 날씨를 직접 받아 온다 (키 없음, CORS 허용).
 *
 * 배포 서버(Vercel)에서는 Open-Meteo 접속이 자주 막혀서, 브라우저가 받은 원본을
 * 백엔드에 넘겨 정리만 맡긴다. 여기서 실패하면 undefined 를 돌려주고,
 * 그때는 백엔드가 직접 조회한다.
 */
const API_URL = 'https://api.open-meteo.com/v1/forecast'
const TTL_MS = 10 * 60 * 1000
const TIMEOUT_MS = 8000

// 백엔드 app/services/weather.py 의 params 와 같아야 한다
const PARAMS = {
  current: 'temperature_2m,apparent_temperature,weather_code',
  hourly: 'temperature_2m,apparent_temperature,precipitation_probability,weather_code',
  daily: 'temperature_2m_max,temperature_2m_min,precipitation_probability_max',
  timezone: 'Asia/Seoul',
  forecast_days: '1',
}

const cache = new Map<string, { at: number; data: unknown }>()

export async function fetchOpenMeteo(lat: number, lon: number): Promise<unknown | undefined> {
  const key = `${lat.toFixed(2)},${lon.toFixed(2)}`
  const hit = cache.get(key)
  if (hit && Date.now() - hit.at < TTL_MS) return hit.data

  const qs = new URLSearchParams({ latitude: String(lat), longitude: String(lon), ...PARAMS })
  try {
    const res = await fetch(`${API_URL}?${qs}`, { signal: AbortSignal.timeout(TIMEOUT_MS) })
    if (!res.ok) return undefined
    const data: unknown = await res.json()
    cache.set(key, { at: Date.now(), data })
    return data
  } catch {
    return undefined
  }
}
