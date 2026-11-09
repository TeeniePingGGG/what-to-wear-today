const KEY = 'wear.accessToken'

export function getToken(): string | null {
  try {
    return localStorage.getItem(KEY)
  } catch {
    return null
  }
}

export function setToken(token: string) {
  localStorage.setItem(KEY, token)
}

export function clearToken() {
  try {
    localStorage.removeItem(KEY)
  } catch {
    /* noop */
  }
}
