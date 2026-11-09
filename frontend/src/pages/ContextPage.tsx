import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { errorMessage } from '../api/client'
import { useCreateRecommendation, useTodayRecommendation } from '../api/recommendations'
import { useAddSchedule, useDeleteSchedule, useSchedules } from '../api/schedules'
import { Icon } from '../components/Icon'
import { useCoords } from '../hooks/useCoords'
import { MOOD_LABEL, type Mood } from '../types/api'
import s from './pages.module.css'

const SITUATIONS = ['등교', '출근', '발표', '면접', '저녁 약속', '데이트', '운동', '여행', '많이 걷기']
const MOODS = Object.keys(MOOD_LABEL) as Mood[]

export default function ContextPage() {
  const navigate = useNavigate()
  const { data: coords } = useCoords()
  const schedules = useSchedules()
  const addSchedule = useAddSchedule()
  const deleteSchedule = useDeleteSchedule()
  const lastRec = useTodayRecommendation().data
  const recommend = useCreateRecommendation()

  // 오늘 이미 추천받았다면 그때 고른 조건으로 시작
  const [picked, setPicked] = useState<string[]>(() => lastRec?.situations ?? [])
  const [mood, setMood] = useState<Mood>(() => lastRec?.mood ?? 'NEAT')
  const [note, setNote] = useState(() => lastRec?.user_note ?? '')

  const [time, setTime] = useState('')
  const [title, setTitle] = useState('')
  const [important, setImportant] = useState(false)

  const toggle = (label: string) => setPicked((p) => (p.includes(label) ? p.filter((x) => x !== label) : [...p, label]))

  const add = (e: FormEvent) => {
    e.preventDefault()
    if (!title.trim()) return
    addSchedule.mutate(
      { title: title.trim(), start_time: time || null, is_important: important },
      {
        onSuccess: () => {
          setTitle('')
          setTime('')
          setImportant(false)
        },
      },
    )
  }

  const submit = () => {
    if (!coords) return
    recommend.mutate(
      {
        latitude: coords.latitude,
        longitude: coords.longitude,
        location_name: coords.name,
        situations: picked,
        mood,
        user_note: note.trim() || null,
      },
      { onSuccess: () => navigate('/') },
    )
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

      <section style={{ display: 'flex', flexDirection: 'column', gap: 10 }} aria-labelledby="sched-title">
        <h2 id="sched-title" className={s.sectionTitle}>
          오늘 일정
        </h2>
        <div className="card" style={{ padding: 0 }}>
          {schedules.data?.length === 0 && (
            <p className={s.subtitle} style={{ padding: '14px 16px', marginTop: 0 }}>
              아직 일정이 없어요. 아래에서 추가해 주세요.
            </p>
          )}
          {schedules.data?.map((sc) => (
            <div key={sc.id} className={s.scheduleRow}>
              <span className={s.scheduleTime}>{sc.start_time ? sc.start_time.slice(0, 5) : '시간 미정'}</span>
              <span style={{ flex: 1, minWidth: 0, fontSize: 15, fontWeight: 600 }} className={s.ellipsis}>
                {sc.title}
              </span>
              {sc.is_important && <span className={s.importantBadge}>주요 일정</span>}
              <button
                type="button"
                className={s.iconLink}
                aria-label={`${sc.title} 삭제`}
                onClick={() => deleteSchedule.mutate(sc.id)}
                disabled={deleteSchedule.isPending}
              >
                <Icon name="close" size={18} />
              </button>
            </div>
          ))}
          <form onSubmit={add} className={s.scheduleForm}>
            <label className={s.timeField}>
              <span className="visually-hidden">시작 시간</span>
              <input type="time" value={time} onChange={(e) => setTime(e.target.value)} />
            </label>
            <label style={{ flex: 1, minWidth: 140 }}>
              <span className="visually-hidden">일정 이름</span>
              <input
                className={s.textInput}
                value={title}
                maxLength={100}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="예: 팀 프로젝트 발표"
              />
            </label>
            <label className={s.checkRow}>
              <input type="checkbox" checked={important} onChange={(e) => setImportant(e.target.checked)} />
              주요 일정
            </label>
            <button type="submit" className="btn" style={{ height: 44 }} disabled={!title.trim() || addSchedule.isPending}>
              <Icon name="plus" size={16} /> 추가
            </button>
          </form>
        </div>
        {(schedules.error || addSchedule.error) && <p className="error-text">{errorMessage(schedules.error ?? addSchedule.error)}</p>}
      </section>

      <section style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
        <h2 className={s.sectionTitle}>
          오늘의 상황 <span className={s.subtitle}>여러 개 선택 가능</span>
        </h2>
        <div className={s.chipRow}>
          {SITUATIONS.map((label) => (
            <button key={label} type="button" className="chip" aria-pressed={picked.includes(label)} onClick={() => toggle(label)}>
              {label}
            </button>
          ))}
        </div>
      </section>

      <section style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
        <h2 className={s.sectionTitle}>원하는 분위기</h2>
        <div className={s.chipRow} role="radiogroup" aria-label="원하는 분위기">
          {MOODS.map((m) => (
            <button key={m} type="button" role="radio" aria-checked={mood === m} className="chip" onClick={() => setMood(m)}>
              {MOOD_LABEL[m]}
            </button>
          ))}
        </div>
      </section>

      <label className="field">
        AI에게 더 알려줄 것
        <textarea rows={3} value={note} onChange={(e) => setNote(e.target.value)} placeholder="예: 오래 앉아 있어요, 이동이 많아요" maxLength={500} />
      </label>

      {recommend.error && (
        <p className={s.notice} role="alert">
          {errorMessage(recommend.error)}
        </p>
      )}
      <button type="button" className="btn btn-primary" onClick={submit} style={{ height: 52 }} disabled={!coords || recommend.isPending}>
        <Icon name="sparkle" size={18} />
        {recommend.isPending ? 'AI가 코디를 고르고 있어요…' : '이 조건으로 코디 추천받기'}
      </button>
    </div>
  )
}
