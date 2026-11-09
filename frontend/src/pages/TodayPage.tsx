import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useMe } from '../api/auth'
import { assetUrl, errorMessage } from '../api/client'
import { useSelectOutfit, useTodayRecommendation } from '../api/recommendations'
import { useSchedules } from '../api/schedules'
import { useWeather } from '../api/weather'
import { Icon } from '../components/Icon'
import { useCoords } from '../hooks/useCoords'
import { CATEGORY_LABEL, type Category, type Outfit, type Schedule } from '../types/api'
import s from './pages.module.css'

const todayLabel = new Intl.DateTimeFormat('ko-KR', { month: 'long', day: 'numeric', weekday: 'long' }).format(new Date())

// 코디 안에서 옷을 보여 줄 순서
const SLOT_ORDER: Category[] = ['OUTER', 'TOP', 'DRESS', 'BOTTOM', 'SHOES', 'BAG', 'ACCESSORY']

const hhmm = (t: string | null) => (t ? t.slice(0, 5) : '')

function scheduleLine(list: Schedule[]): string {
  if (list.length === 0) return '오늘 일정 추가하기'
  const main = list.find((x) => x.is_important) ?? list[0]
  const rest = list.length > 1 ? ` 외 ${list.length - 1}개` : ''
  return `${main.start_time ? `${hhmm(main.start_time)} ` : ''}${main.title}${rest}`
}

export default function TodayPage() {
  const { data: me } = useMe()
  const { data: coords } = useCoords()
  const weather = useWeather(coords)
  const schedules = useSchedules()
  const rec = useTodayRecommendation()
  const select = useSelectOutfit()
  // 사용자가 넘겨 본 조합 번호 (새 추천을 받으면 처음부터)
  const [picked, setPicked] = useState<{ recId: number; index: number } | null>(null)

  const w = weather.data
  const outfits = rec.data?.outfits ?? []
  const selectedIndex = outfits.findIndex((o) => o.is_selected)
  // 처음엔 '입기로 한' 코디부터, 없으면 1번부터 보여 줌
  const pickedIndex = picked && picked.recId === rec.data?.id ? picked.index : null
  const index = Math.min(pickedIndex ?? Math.max(selectedIndex, 0), Math.max(outfits.length - 1, 0))
  const current: Outfit | undefined = outfits[index]
  const items = current ? [...current.items].sort((a, b) => SLOT_ORDER.indexOf(a.slot) - SLOT_ORDER.indexOf(b.slot)) : []
  const chosen = outfits.find((o) => o.is_selected)

  return (
    <div className={s.page}>
      <header className={s.header}>
        <div>
          <p className={s.subtitle}>
            {todayLabel}
            {w && ` · ${w.location_name ?? '현재 위치'}`}
          </p>
          <h1 className={s.title}>{me ? `${me.nickname}님, 오늘 뭐 입지?` : '오늘 뭐 입지?'}</h1>
        </div>
      </header>

      <div className={s.todayGrid}>
        <div className={s.todayCol}>
          <section className="card" aria-label="오늘 날씨" aria-busy={weather.isLoading}>
            {weather.error ? (
              <p className="error-text">{errorMessage(weather.error)}</p>
            ) : !w ? (
              <p className={s.subtitle}>날씨를 불러오는 중…</p>
            ) : (
              <>
                <div className={s.weatherMain}>
                  <div className={s.temp}>{w.temp}°</div>
                  <div>
                    <div style={{ fontSize: 15, fontWeight: 600 }}>{w.summary}</div>
                    <div className={s.subtitle}>
                      최고 {w.temp_max}° · 최저 {w.temp_min}°
                    </div>
                  </div>
                </div>
                <div className={s.statGrid}>
                  <div className={s.stat}>
                    <div className={s.statLabel}>체감</div>
                    <div className={s.statValue}>{w.feels_like}°</div>
                  </div>
                  <div className={`${s.stat} ${w.rain_from !== null ? s.statRain : ''}`}>
                    <div className={s.statLabel}>강수{w.rain_from !== null ? ` · ${w.rain_from}시~` : ''}</div>
                    <div className={s.statValue}>{w.pop_rest}%</div>
                  </div>
                  <div className={s.stat}>
                    <div className={s.statLabel}>일교차</div>
                    <div className={s.statValue}>{w.temp_range}°</div>
                  </div>
                </div>
                {coords && !coords.fromDevice && (
                  <p className={s.subtitle} style={{ marginTop: 10 }}>
                    위치 권한을 허용하면 지금 있는 곳의 날씨로 바뀌어요.
                  </p>
                )}
              </>
            )}
          </section>

          <Link to="/context" className={s.rowLink}>
            <span className={s.iconBadge}>
              <Icon name="calendar" />
            </span>
            <span style={{ flex: 1, minWidth: 0 }}>
              <span className={s.subtitle} style={{ display: 'block', marginTop: 0 }}>
                오늘 일정 · 눌러서 수정
              </span>
              <span className={s.ellipsis} style={{ display: 'block', fontSize: 15, fontWeight: 600 }}>
                {schedules.data ? scheduleLine(schedules.data) : '…'}
              </span>
            </span>
            <Icon name="chevronRight" size={18} />
          </Link>
        </div>

        <section className="card" style={{ borderRadius: 'var(--radius-xl)', padding: 18 }} aria-labelledby="outfit-title">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 8 }}>
            <h2 id="outfit-title" className={s.sectionTitle} style={{ fontSize: 18 }}>
              오늘의 추천 코디
            </h2>
            {outfits.length > 0 && (
              <span className={s.countBadge}>
                {index + 1} / {outfits.length} 조합
              </span>
            )}
          </div>

          {rec.isLoading && <p className={s.subtitle}>불러오는 중…</p>}
          {rec.error && <p className="error-text">{errorMessage(rec.error)}</p>}

          {rec.data === null && (
            <div className={s.empty} style={{ padding: '32px 8px' }}>
              <Icon name="sparkle" size={28} />
              <p>오늘 날씨와 일정에 맞춰 내 옷장에서 코디를 골라 드려요.</p>
              <Link to="/context" className="btn btn-primary">
                오늘 코디 추천받기
              </Link>
            </div>
          )}

          {current && (
            <>
              <div className={s.outfitItems}>
                {items.map(({ slot, clothing_item: c }) => (
                  <div key={c.id}>
                    <div className={s.outfitThumb}>
                      <img src={assetUrl(c.image_url)} alt={c.name} className={s.outfitImg} />
                    </div>
                    <div className={s.itemName}>{c.name}</div>
                    <div className={s.itemSub}>
                      {CATEGORY_LABEL[slot]}
                      {c.color_name && ` · ${c.color_name}`}
                    </div>
                  </div>
                ))}
              </div>

              <div className={s.reasonBox}>
                {current.summary && <p>{current.summary}</p>}
                <Link to={`/guide/${current.id}`} style={{ fontSize: 13, fontWeight: 600, textDecoration: 'none' }}>
                  스타일리스트 설명 보기 →
                </Link>
              </div>

              {select.error && <p className="error-text">{errorMessage(select.error)}</p>}
              <div className={s.actions}>
                <button
                  type="button"
                  className="btn"
                  disabled={outfits.length < 2}
                  onClick={() => rec.data && setPicked({ recId: rec.data.id, index: (index + 1) % outfits.length })}
                >
                  <Icon name="refresh" size={16} /> 다른 조합
                </button>
                {current.is_selected ? (
                  <span className={`btn ${s.chosen}`} style={{ flex: 1.6 }} role="status">
                    입기로 했어요 ✓
                  </span>
                ) : (
                  <button
                    type="button"
                    className="btn btn-primary"
                    style={{ flex: 1.6 }}
                    disabled={select.isPending}
                    onClick={() => select.mutate(current.id)}
                  >
                    {chosen ? '이걸로 바꿀게요' : '이걸로 입을게요'}
                  </button>
                )}
              </div>
              <Link to="/context" className={s.subtitle} style={{ display: 'block', textAlign: 'center', marginTop: 12 }}>
                일정·상황을 바꿔서 다시 추천받기
              </Link>
            </>
          )}
        </section>
      </div>
    </div>
  )
}
