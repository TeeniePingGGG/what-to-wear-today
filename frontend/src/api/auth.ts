import { useQuery } from '@tanstack/react-query'
import type { TokenResponse, User } from '../types/api'
import { getToken } from '../auth/token'
import { api } from './client'

export async function signup(body: { email: string; password: string; nickname: string }) {
  const { data } = await api.post<TokenResponse>('/auth/signup', body)
  return data
}

export async function login(body: { email: string; password: string }) {
  const { data } = await api.post<TokenResponse>('/auth/login', body)
  return data
}

export function useMe() {
  return useQuery({
    queryKey: ['me'],
    queryFn: async () => (await api.get<User>('/auth/me')).data,
    enabled: !!getToken(),
    staleTime: 5 * 60 * 1000,
  })
}
