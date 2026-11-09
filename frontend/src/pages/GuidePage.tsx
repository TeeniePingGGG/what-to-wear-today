import { useEffect, useRef, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { assetUrl, errorMessage } from '../api/client'
import { useDeleteFeedback, useGenerateGuide, useOutfit, useSaveFeedback } from '../api/outfits'
import { Icon } from '../components/Icon'
import { FEEDBACK_REASONS, MOOD_LABEL, type FeedbackRating, type FeedbackReason, type OutfitDetail } from '../types/api'
import s from './pages.module.css'

// 이유 태그별 색
const TONE: Record<string, { color: string; background: string }> = {
  기온: { color: 'var(--color-warm-ink)', background: 'var(--color-warm-soft)' },
  비: { color: 'var(--color-rain-ink)', background: 'var(--color-rain-soft)' },
  일정: { color: 'var(--color-primary)', background: 'var(--color-primary-soft)' },
}
const NEUTRAL = { color: 'var(--color-text)', background: 'var(--color-surface-muted)' }

const SLOT_ORDER = ['OUTER', 'TOP', 'DRESS', 'BOTTOM', 'SHOES', 'BAG', 'ACCESSORY']

export default function GuidePage() {
  const outfitId = Number(useParams().outfitId)
  const { data, isLoading, error } = useOutfit(outfitId)
  const guide = useGenerateGuide(outfitId)

  // 가이드가 아직 없으면 화면에 들어오자마자 한 번 만들기
  const requested = useRef(false)
  useEffect(() => {
    if (data && !data.reasons && !requested.current) {
      requested.current = true
      guide.mutate(false)
    }
  }, [data, guide])

  if (isLoading) return <p className={s.subtitle}>불러오는 중…</p>
  if (error || !data) return <p className="error-text">{errorMessage(error)}</p>

  const rec = data.recommendation
  const items = [...data.items].sort((a, b) => SLOT_ORDER.indexOf(a.slot) - SLOT_ORDER.indexOf(b.slot))
  const date = new Date(rec.target_date)
  const conditions = [
    rec.location_name,
    rec.weather?.summary,
    rec.weather && `체감 ${rec.weather.feels_like}°`,
    rec.situations.length ? rec.situations.join('·') : null,
    rec.mood ? MOOD_LABEL[rec.mood] : null,
  ].filter(Boolean)

  return (
    <div className={`${s.page} ${s.narrow}`}>
      <div className={s.backRow}>
        <Link to="/" aria-label="뒤로" className={s.iconLink}>
          <Icon name="chevronLeft" size={22} />
        </Link>
        <h1 className={s.title} style={{ fontSize: 20 }}>
          스타일리스트 노트
        </h1>
      </div>

      <section className="card" aria-label="이 코디">
        <p className={s.subtitle} style={{ marginTop: 0 }}>
          {date.getMonth() + 1}월 {date.getDate()}일 · {conditions.join(' · ')}
        </p>
        <div className={s.guideItems}>
          {items.map(({ clothing_item: c }) => (
            <div key={c.id} className={s.guideItem}>
              <div className={s.outfitThumb}>
                <img src={assetUrl(c.image_url)} alt="" className={s.outfitImg} />
              </div>
              <span className={s.itemName}>{c.name}</span>
            </div>
          ))}
        </div>
      </section>

      {!data.reasons && (guide.isPending || !guide.error) && (
        <p className={s.aiNotice} role="status">
          <Icon name="sparkle" size={16} /> 스타일리스트가 오늘 코디 설명을 쓰고 있어요…
        </p>
      )}
      {guide.error && (
        <div className={s.notice} role="alert">
          <p>{errorMessage(guide.error)}</p>
          <button type="button" className="btn" style={{ height: 40, marginTop: 8 }} onClick={() => guide.mutate(!!data.reasons)}>
            <Icon name="refresh" size={16} /> 다시 시도
          </button>
        </div>
      )}

      {data.reasons && (
        <>
          {data.intro && (
            <div style={{ display: 'flex', gap: 12, alignItems: 'flex-start' }}>
              <span className={s.stylistAvatar} aria-hidden="true">
                <Icon name="sparkle" size={20} />
              </span>
              <p className={s.bubble}>{data.intro}</p>
            </div>
          )}

          <section className="card" style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <h2 className={s.sectionTitle}>왜 이 조합일까요?</h2>
            {data.reasons.map((r, i) => (
              <div key={i} className={s.reasonRow}>
                <span className={s.reasonTag} style={TONE[r.tag] ?? NEUTRAL}>
                  {r.tag}
                </span>
                <div>
                  <div style={{ fontSize: 14, fontWeight: 600 }}>{r.title}</div>
                  <div style={{ fontSize: 13, color: 'var(--color-text-sub)', lineHeight: 1.5, marginTop: 2 }}>{r.body}</div>
                </div>
              </div>
            ))}
          </section>

          {data.tips && data.tips.length > 0 && (
            <section className="card" style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              <h2 className={s.sectionTitle}>스타일링 팁</h2>
              <ol className={s.tips}>
                {data.tips.map((t) => (
                  <li key={t}>{t}</li>
                ))}
              </ol>
            </section>
          )}

          <button
            type="button"
            className={s.textButton}
            onClick={() => guide.mutate(true)}
            disabled={guide.isPending}
          >
            <Icon name="refresh" size={14} /> {guide.isPending ? '다시 쓰는 중…' : '설명 다시 받기'}
          </button>
        </>
      )}

      {/* 피드백이 바뀌면 폼을 새 값으로 다시 시작 */}
      <FeedbackForm key={data.feedback?.updated_at ?? 'new'} outfit={data} />
    </div>
  )
}

function FeedbackForm({ outfit }: { outfit: OutfitDetail }) {
  const save = useSaveFeedback(outfit.id)
  const remove = useDeleteFeedback(outfit.id)
  const saved = outfit.feedback

  const [rating, setRating] = useState<FeedbackRating | null>(saved?.rating ?? null)
  const [reasons, setReasons] = useState<FeedbackReason[]>(saved?.reasons ?? [])
  const [comment, setComment] = useState(saved?.comment ?? '')
  const [laundry, setLaundry] = useState<number[]>([])

  const toggle = <T,>(list: T[], v: T) => (list.includes(v) ? list.filter((x) => x !== v) : [...list, v])
  const dirty =
    rating !== (saved?.rating ?? null) ||
    reasons.join() !== (saved?.reasons ?? []).join() ||
    comment.trim() !== (saved?.comment ?? '') ||
    laundry.length > 0

  const submit = () => {
    if (!rating) return
    save.mutate({
      rating,
      reasons: rating === 'DISLIKE' ? reasons : [],
      comment: comment.trim() || null,
      laundry_item_ids: rating === 'DISLIKE' && reasons.includes('IN_LAUNDRY') ? laundry : [],
    })
  }

  return (
    <section className="card" style={{ display: 'flex', flexDirection: 'column', gap: 12 }} aria-labelledby="fb-title">
      <h2 id="fb-title" className={s.sectionTitle}>
        이 코디, 어떠세요?
      </h2>
      <div className={s.actions} style={{ marginTop: 0 }}>
        <button
          type="button"
          className={rating === 'LIKE' ? 'btn btn-primary' : 'btn'}
          aria-pressed={rating === 'LIKE'}
          onClick={() => setRating(rating === 'LIKE' ? null : 'LIKE')}
        >
          마음에 들어요
        </button>
        <button
          type="button"
          className={rating === 'DISLIKE' ? 'btn btn-primary' : 'btn'}
          aria-pressed={rating === 'DISLIKE'}
          onClick={() => setRating(rating === 'DISLIKE' ? null : 'DISLIKE')}
        >
          아쉬워요
        </button>
      </div>

      {rating === 'DISLIKE' && (
        <fieldset style={{ border: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: 8 }}>
          <legend className={s.subtitle} style={{ marginBottom: 8 }}>
            어떤 점이 아쉬웠나요? (여러 개 선택 가능)
          </legend>
          <div className={s.chipRow}>
            {(Object.keys(FEEDBACK_REASONS) as FeedbackReason[]).map((r) => (
              <button key={r} type="button" className="chip" aria-pressed={reasons.includes(r)} onClick={() => setReasons(toggle(reasons, r))}>
                {FEEDBACK_REASONS[r]}
              </button>
            ))}
          </div>
          {reasons.includes('IN_LAUNDRY') && (
            <div className={s.laundryBox}>
              <p className={s.subtitle} style={{ marginTop: 0 }}>
                세탁 중인 옷을 골라 주세요. 세탁이 끝날 때까지 추천에서 빠져요.
              </p>
              <div className={s.chipRow}>
                {outfit.items.map(({ clothing_item: c }) => (
                  <button key={c.id} type="button" className="chip" aria-pressed={laundry.includes(c.id)} onClick={() => setLaundry(toggle(laundry, c.id))}>
                    {c.name}
                  </button>
                ))}
              </div>
            </div>
          )}
        </fieldset>
      )}

      {rating && (
        <label className="field">
          스타일리스트에게 한마디 (선택)
          <textarea rows={2} maxLength={500} value={comment} onChange={(e) => setComment(e.target.value)} placeholder="예: 아침엔 생각보다 추웠어요" />
        </label>
      )}

      {(save.error || remove.error) && <p className="error-text">{errorMessage(save.error ?? remove.error)}</p>}

      {rating && dirty && (
        <button type="button" className="btn btn-primary" onClick={submit} disabled={save.isPending}>
          {save.isPending ? '보내는 중…' : saved ? '피드백 수정하기' : '피드백 보내기'}
        </button>
      )}
      {saved && !dirty && (
        <div className={s.savedRow} role="status">
          <span>고마워요! 다음 추천에 반영할게요.</span>
          <button type="button" className={s.textButton} onClick={() => remove.mutate()} disabled={remove.isPending}>
            피드백 취소
          </button>
        </div>
      )}
      {!saved && !rating && <p className={s.subtitle}>남긴 피드백은 다음 추천에 반영돼요.</p>}
    </section>
  )
}
