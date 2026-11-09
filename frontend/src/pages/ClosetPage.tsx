import { useState } from 'react'
import { Link } from 'react-router-dom'
import { assetUrl, errorMessage } from '../api/client'
import { useClothes } from '../api/clothes'
import { Icon } from '../components/Icon'
import { CATEGORY_LABEL, SEASON_LABEL, type Category } from '../types/api'
import s from './pages.module.css'

const TABS: (Category | 'ALL')[] = ['ALL', 'TOP', 'BOTTOM', 'OUTER', 'SHOES', 'ACCESSORY']

export default function ClosetPage() {
  const [tab, setTab] = useState<Category | 'ALL'>('ALL')
  const { data, isLoading, error } = useClothes(tab === 'ALL' ? {} : { category: tab })

  return (
    <div className={s.page}>
      <header className={s.header}>
        <div>
          <h1 className={s.title}>내 옷장</h1>
          <p className={s.subtitle}>{data ? `${data.length}벌` : ' '}</p>
        </div>
        <Link to="/closet/new" className="btn btn-primary" style={{ height: 40 }}>
          <Icon name="plus" size={16} strokeWidth={2.2} /> 옷 등록
        </Link>
      </header>

      <div className={s.tabs} role="tablist" aria-label="카테고리">
        {TABS.map((t) => (
          <button
            key={t}
            type="button"
            role="tab"
            aria-selected={tab === t}
            className="chip"
            style={{ height: 36, flexShrink: 0 }}
            onClick={() => setTab(t)}
          >
            {t === 'ALL' ? '전체' : CATEGORY_LABEL[t]}
          </button>
        ))}
      </div>

      {isLoading && <p className={s.subtitle}>불러오는 중…</p>}
      {error && <p className="error-text">{errorMessage(error)}</p>}

      {data && data.length === 0 && (
        <div className={`card ${s.empty}`}>
          <p>아직 등록된 옷이 없어요.</p>
          <Link to="/closet/new" className="btn btn-primary">
            첫 옷 등록하기
          </Link>
        </div>
      )}

      {data && data.length > 0 && (
        <div className={s.closetGrid}>
          {data.map((item) => (
            <article key={item.id} className={s.closetCard}>
              <img className={s.closetImg} src={assetUrl(item.image_url)} alt={item.name} loading="lazy" />
              <div style={{ padding: '0 2px' }}>
                <div className={s.ellipsis} style={{ fontSize: 13, fontWeight: 600 }}>
                  {item.name}
                </div>
                <div className={`${s.ellipsis} ${s.itemSub}`} style={{ textAlign: 'left' }}>
                  {[item.color_name, item.seasons.map((x) => SEASON_LABEL[x]).join('/')].filter(Boolean).join(' · ')}
                </div>
              </div>
            </article>
          ))}
        </div>
      )}
    </div>
  )
}
