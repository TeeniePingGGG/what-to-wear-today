import { NavLink, Outlet } from 'react-router-dom'
import { Icon, type IconName } from '../Icon'
import styles from './AppLayout.module.css'

const NAV: { to: string; label: string; icon: IconName }[] = [
  { to: '/', label: '오늘', icon: 'home' },
  { to: '/closet', label: '옷장', icon: 'closet' },
  { to: '/closet/new', label: '등록', icon: 'plusSquare' },
  { to: '/my', label: '마이', icon: 'user' },
]

/**
 * 반응형 레이아웃
 * - 모바일/태블릿(<1024px): 하단 탭바
 * - 데스크톱(≥1024px): 왼쪽 사이드바
 */
export default function AppLayout() {
  return (
    <div className={styles.shell}>
      <nav className={styles.nav} aria-label="주 메뉴">
        <div className={styles.brand}>오늘 뭐 입지?</div>
        {NAV.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end
            className={({ isActive }) => (isActive ? `${styles.link} ${styles.active}` : styles.link)}
          >
            <Icon name={item.icon} size={22} />
            <span>{item.label}</span>
          </NavLink>
        ))}
      </nav>
      <main className={styles.main}>
        <Outlet />
      </main>
    </div>
  )
}
