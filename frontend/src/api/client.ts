import axios, { AxiosError } from 'axios'
import { clearToken, getToken } from '../auth/token'

// 개발: vite proxy 가 /api → localhost:8000 으로 전달
// 배포: VITE_API_BASE_URL 에 백엔드 주소 지정 (예: https://api.example.com)
export const API_BASE = import.meta.env.VITE_API_BASE_URL ?? ''

export const api = axios.create({ baseURL: `${API_BASE}/api` })

api.interceptors.request.use((config) => {
  const token = getToken()
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  (res) => res,
  (error: AxiosError) => {
    if (error.response?.status === 401 && !location.pathname.startsWith('/login')) {
      clearToken()
      location.assign('/login')
    }
    return Promise.reject(error)
  },
)

/** FastAPI 에러 응답에서 사용자에게 보여줄 메시지 추출 */
export function errorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = (error.response?.data as { detail?: unknown } | undefined)?.detail
    if (typeof detail === 'string') return detail
    if (Array.isArray(detail)) return '입력값을 다시 확인해 주세요.'
    if (!error.response) return '서버에 연결할 수 없어요. 백엔드가 켜져 있는지 확인해 주세요.'
  }
  return '알 수 없는 오류가 발생했어요.'
}

/** /uploads/... 상대 경로를 실제 이미지 주소로 */
export function assetUrl(path: string) {
  return path.startsWith('http') ? path : `${API_BASE}${path}`
}
