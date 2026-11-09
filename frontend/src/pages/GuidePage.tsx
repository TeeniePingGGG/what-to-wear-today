import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Icon } from '../components/Icon'
import { sampleOutfit } from '../mocks/today'
import s from './pages.module.css'

const TONE = {
  warm: { color: 'var(--color-warm-ink)', background: 'var(--color-warm-soft)' },
  rain: { color: 'var(--color-rain-ink)', background: 'var(--color-rain-soft)' },
  primary: { color: 'var(--color-primary)', background: 'var(--color-primary-soft)' },
} as const

const DISLIKE_REASONS = [
  { value: 'TOO_COLD', label: '추울 것 같아요' },
  { value: 'TOO_FORMAL', label: '너무 격식 있어요' },
  { value: 'IN_LAUNDRY', label: '이 옷은 세탁 중' },
]

export default function GuidePage() {
  // TODO(기능3): useParams 의 outfitId 로 GET /api/outfits/:id 조회
  const outfit = sampleOutfit
  const [vote, setVote] = useState<'LIKE' | 'DISLIKE' | null>(null)
  const [reasons, setReasons] = useState<string[]>([])

  return (
    <div className={`${s.page} ${s.narrow}`}>
      <div className={s.backRow}>
        <Link to="/" aria-label="뒤로" className={s.iconLink}>
          <Icon name="chevronLeft" size={22} />
        </Link>
        <h1 className={s.title} style={{ fontSize: 20 }}>
          스타일리스트 노트
        </h1>
        <span className={s.sampleBadge} style={{ marginLeft: 'auto' }}>
          샘플 데이터
        </span>
      </div>

      <section className="card" style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        <h2 className={s.sectionTitle}>왜 이 조합일까요?</h2>
        {outfit.reasons.map((r) => (
          <div key={r.tag} className={s.reasonRow}>
            <span className={s.reasonTag} style={TONE[r.tone]}>
              {r.tag}
            </span>
            <div>
              <div style={{ fontSize: 14, fontWeight: 600 }}>{r.title}</div>
              <div style={{ fontSize: 13, color: 'var(--color-text-sub)', lineHeight: 1.5, marginTop: 2 }}>{r.body}</div>
            </div>
          </div>
        ))}
      </section>

      <section className="card" style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
        <h2 className={s.sectionTitle}>스타일링 팁</h2>
        <ol className={s.tips}>
          {outfit.tips.map((t) => (
            <li key={t}>{t}</li>
          ))}
        </ol>
      </section>

      <section className="card" style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        <h2 className={s.sectionTitle}>이 코디, 어떠세요?</h2>
        <div className={s.actions} style={{ marginTop: 0 }}>
          <button
            type="button"
            className={vote === 'LIKE' ? 'btn btn-primary' : 'btn'}
            aria-pressed={vote === 'LIKE'}
            onClick={() => setVote(vote === 'LIKE' ? null : 'LIKE')}
          >
            마음에 들어요
          </button>
          <button
            type="button"
            className={vote === 'DISLIKE' ? 'btn btn-primary' : 'btn'}
            aria-pressed={vote === 'DISLIKE'}
            onClick={() => setVote(vote === 'DISLIKE' ? null : 'DISLIKE')}
          >
            아쉬워요
          </button>
        </div>
        {vote === 'DISLIKE' && (
          <div className={s.chipRow}>
            {DISLIKE_REASONS.map((r) => (
              <button
                key={r.value}
                type="button"
                className="chip"
                aria-pressed={reasons.includes(r.value)}
                onClick={() =>
                  setReasons((p) => (p.includes(r.value) ? p.filter((x) => x !== r.value) : [...p, r.value]))
                }
              >
                {r.label}
              </button>
            ))}
          </div>
        )}
        <p className={s.subtitle}>남긴 피드백은 다음 추천에 반영돼요.</p>
      </section>
    </div>
  )
}
