import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Icon } from '../components/Icon'
import s from './pages.module.css'

const SITUATIONS = ['등교', '출근', '발표', '면접', '저녁 약속', '데이트', '운동', '여행', '많이 걷기']
const MOODS = [
  { value: 'COMFY', label: '편하게' },
  { value: 'NEAT', label: '단정하게' },
  { value: 'DRESSY', label: '꾸민 듯' },
] as const

export default function ContextPage() {
  const navigate = useNavigate()
  const [picked, setPicked] = useState<string[]>([])
  const [mood, setMood] = useState<(typeof MOODS)[number]['value']>('NEAT')
  const [note, setNote] = useState('')

  const toggle = (label: string) =>
    setPicked((p) => (p.includes(label) ? p.filter((x) => x !== label) : [...p, label]))

  const submit = () => {
    // TODO(기능2): POST /api/recommendations { situations: picked, mood, user_note: note, lat, lon }
    console.log({ situations: picked, mood, user_note: note })
    navigate('/')
  }

  return (
    <div className={`${s.page} ${s.narrow}`}>
      <div className={s.backRow}>
        <Link to="/" aria-label="뒤로" className={s.iconLink}>
          <Icon name="chevronLeft" size={22} />
        </Link>
        <h1 className={s.title} style={{ fontSize: 20 }}>
          오늘 어떤 하루인가요?
        </h1>
      </div>

      <section style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
        <h2 className={s.sectionTitle}>
          오늘의 상황 <span className={s.subtitle}>여러 개 선택 가능</span>
        </h2>
        <div className={s.chipRow}>
          {SITUATIONS.map((label) => (
            <button
              key={label}
              type="button"
              className="chip"
              aria-pressed={picked.includes(label)}
              onClick={() => toggle(label)}
            >
              {label}
            </button>
          ))}
        </div>
      </section>

      <section style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
        <h2 className={s.sectionTitle}>원하는 분위기</h2>
        <div className={s.chipRow} role="radiogroup" aria-label="원하는 분위기">
          {MOODS.map((m) => (
            <button
              key={m.value}
              type="button"
              role="radio"
              aria-checked={mood === m.value}
              aria-pressed={mood === m.value}
              className="chip"
              onClick={() => setMood(m.value)}
            >
              {m.label}
            </button>
          ))}
        </div>
      </section>

      <label className="field">
        AI에게 더 알려줄 것
        <textarea
          rows={3}
          value={note}
          onChange={(e) => setNote(e.target.value)}
          placeholder="예: 오래 앉아 있어요, 이동이 많아요"
          maxLength={500}
        />
      </label>

      <button type="button" className="btn btn-primary" onClick={submit} style={{ height: 52 }}>
        <Icon name="sparkle" size={18} /> 이 조건으로 코디 추천받기
      </button>
    </div>
  )
}
