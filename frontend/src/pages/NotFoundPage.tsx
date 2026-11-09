import { Link } from 'react-router-dom'
import s from './pages.module.css'

export default function NotFoundPage() {
  return (
    <div className={s.authWrap}>
      <div className={`card ${s.authCard}`} style={{ textAlign: 'center' }}>
        <h1 className={s.title}>페이지를 찾을 수 없어요</h1>
        <Link to="/" className="btn btn-primary">
          홈으로
        </Link>
      </div>
    </div>
  )
}
