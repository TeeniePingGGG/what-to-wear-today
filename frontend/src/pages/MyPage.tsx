import { useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { useMe } from '../api/auth'
import { clearToken } from '../auth/token'
import { Icon } from '../components/Icon'
import s from './pages.module.css'

export default function MyPage() {
  const { data: me } = useMe()
  const qc = useQueryClient()
  const navigate = useNavigate()

  const logout = () => {
    clearToken()
    qc.clear()
    navigate('/login', { replace: true })
  }

  return (
    <div className={`${s.page} ${s.narrow}`}>
      <h1 className={s.title}>마이</h1>
      <section className="card" style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
        <div style={{ fontSize: 18, fontWeight: 700 }}>{me?.nickname ?? '…'}</div>
        <div className={s.subtitle}>{me?.email}</div>
      </section>
      {/* TODO: 기본 위치, 선호 스타일 설정 */}
      <button type="button" className="btn" onClick={logout}>
        <Icon name="logout" size={18} /> 로그아웃
      </button>
    </div>
  )
}
