import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { signup } from '../api/auth'
import { errorMessage } from '../api/client'
import { setToken } from '../auth/token'
import s from './pages.module.css'

export default function SignupPage() {
  const navigate = useNavigate()
  const [form, setForm] = useState({ email: '', password: '', nickname: '' })
  const [error, setError] = useState<string | null>(null)
  const [pending, setPending] = useState(false)

  const submit = async (e: FormEvent) => {
    e.preventDefault()
    setPending(true)
    setError(null)
    try {
      const { access_token } = await signup(form)
      setToken(access_token)
      navigate('/', { replace: true })
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setPending(false)
    }
  }

  return (
    <div className={s.authWrap}>
      <form className={`card ${s.authCard}`} onSubmit={submit}>
        <h1 className={s.title}>회원가입</h1>
        <label className="field">
          닉네임
          <input required maxLength={30} value={form.nickname} onChange={(e) => setForm({ ...form, nickname: e.target.value })} />
        </label>
        <label className="field">
          이메일
          <input
            type="email"
            autoComplete="email"
            required
            value={form.email}
            onChange={(e) => setForm({ ...form, email: e.target.value })}
          />
        </label>
        <label className="field">
          비밀번호 (8자 이상)
          <input
            type="password"
            autoComplete="new-password"
            required
            minLength={8}
            maxLength={72}
            value={form.password}
            onChange={(e) => setForm({ ...form, password: e.target.value })}
          />
        </label>
        {error && <p className="error-text">{error}</p>}
        <button type="submit" className="btn btn-primary" disabled={pending}>
          {pending ? '가입 중…' : '가입하기'}
        </button>
        <p className={s.subtitle} style={{ textAlign: 'center' }}>
          이미 계정이 있나요? <Link to="/login">로그인</Link>
        </p>
      </form>
    </div>
  )
}
