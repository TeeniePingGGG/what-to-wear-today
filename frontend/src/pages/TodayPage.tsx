import { Link } from 'react-router-dom'
import { useMe } from '../api/auth'
import { Icon } from '../components/Icon'
import { CLOTH_SHAPES, sampleOutfit, sampleSchedule, sampleWeather } from '../mocks/today'
import s from './pages.module.css'

const todayLabel = new Intl.DateTimeFormat('ko-KR', { month: 'long', day: 'numeric', weekday: 'long' }).format(new Date())

export default function TodayPage() {
  const { data: me } = useMe()
  const w = sampleWeather

  return (
    <div className={s.page}>
      <header className={s.header}>
        <div>
          <p className={s.subtitle}>
            {todayLabel} · {w.location}
          </p>
          <h1 className={s.title}>{me ? `${me.nickname}님, 오늘 뭐 입지?` : '오늘 뭐 입지?'}</h1>
        </div>
        <span className={s.sampleBadge}>샘플 데이터</span>
      </header>

      <div className={s.todayGrid}>
        <div className={s.todayCol}>
          <section className="card" aria-label="오늘 날씨">
            <div className={s.weatherMain}>
              <div className={s.temp}>{w.temp}°</div>
              <div>
                <div style={{ fontSize: 15, fontWeight: 600 }}>{w.sky}</div>
                <div className={s.subtitle}>
                  최고 {w.max}° · 최저 {w.min}°
                </div>
              </div>
            </div>
            <div className={s.statGrid}>
              <div className={s.stat}>
                <div className={s.statLabel}>체감</div>
                <div className={s.statValue}>{w.feelsLike}°</div>
              </div>
              <div className={`${s.stat} ${s.statRain}`}>
                <div className={s.statLabel}>강수 · {w.rainFrom}</div>
                <div className={s.statValue}>{w.pop}%</div>
              </div>
              <div className={s.stat}>
                <div className={s.statLabel}>일교차</div>
                <div className={s.statValue}>{w.max - w.min}°</div>
              </div>
            </div>
          </section>

          <Link to="/context" className={s.rowLink}>
            <span className={s.iconBadge}>
              <Icon name="calendar" />
            </span>
            <span style={{ flex: 1, minWidth: 0 }}>
              <span className={s.subtitle} style={{ display: 'block', marginTop: 0 }}>
                오늘 일정 · 눌러서 수정
              </span>
              <span style={{ display: 'block', fontSize: 15, fontWeight: 600 }}>
                {sampleSchedule.time} {sampleSchedule.title} · {sampleSchedule.hint}
              </span>
            </span>
            <Icon name="chevronRight" size={18} />
          </Link>
        </div>

        <section className="card" style={{ borderRadius: 'var(--radius-xl)', padding: 18 }} aria-labelledby="outfit-title">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h2 id="outfit-title" className={s.sectionTitle} style={{ fontSize: 18 }}>
              오늘의 추천 코디
            </h2>
            <span className={s.sampleBadge} style={{ color: 'var(--color-primary)', background: 'var(--color-primary-soft)' }}>
              1 / 3 조합
            </span>
          </div>

          <div className={s.outfitItems}>
            {sampleOutfit.items.map((item) => (
              <div key={item.name}>
                <div className={s.outfitThumb}>
                  <svg aria-hidden="true" width="60%" viewBox="0 0 64 64">
                    <path d={CLOTH_SHAPES[item.shape]} fill={item.color} stroke="#15171A" strokeWidth="1.6" strokeLinejoin="round" />
                  </svg>
                </div>
                <div className={s.itemName}>{item.name}</div>
                <div className={s.itemSub}>{item.sub}</div>
              </div>
            ))}
          </div>

          <div className={s.reasonBox}>
            <p>{sampleOutfit.summary}</p>
            <Link to={`/guide/${sampleOutfit.id}`} style={{ fontSize: 13, fontWeight: 600, textDecoration: 'none' }}>
              스타일리스트 설명 보기 →
            </Link>
          </div>

          <div className={s.actions}>
            <button type="button" className="btn">
              <Icon name="refresh" size={16} /> 다른 조합
            </button>
            <button type="button" className="btn btn-primary" style={{ flex: 1.6 }}>
              이걸로 입을게요
            </button>
          </div>
        </section>
      </div>
    </div>
  )
}
