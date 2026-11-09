import { useState, type FormEvent } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { login } from '../api/auth'
import { errorMessage } from '../api/client'
import { setToken } from '../auth/token'
import s from './pages.module.css'

export default function LoginPage() {
  const navigate = useNavigate()
  const from = (useLocation().state as { from?: string } | null)?.from ?? '/'
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [pending, setPending] = useState(false)

  const submit = async (e: FormEvent) => {
    e.preventDefault()
    setPending(true)
    setError(null)
    try {
      const { access_token } = await login({ email, password })
      setToken(access_token)
      navigate(from, { replace: true })
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setPending(false)
    }
  }

  return (
    <div className={s.authWrap}>
      <form className={`card ${s.authCard}`} onSubmit={submit}>
        <h1 className={s.title}>오늘 뭐 입지?</h1>
        <p className={s.subtitle}>내 옷장과 오늘 날씨로 코디를 추천받아요.</p>
        <label className="field">
          이메일
          <input type="email" autoComplete="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
        </label>
        <label className="field">
          비밀번호
          <input
            type="password"
            autoComplete="current-password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </label>
        {error && <p className="error-text">{error}</p>}
        <button type="submit" className="btn btn-primary" disabled={pending}>
          {pending ? '로그인 중…' : '로그인'}
        </button>
        <p className={s.subtitle} style={{ textAlign: 'center' }}>
          처음이신가요? <Link to="/signup">회원가입</Link>
        </p>
      </form>
    </div>
  )
}
