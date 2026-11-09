import { useEffect, useRef, useState, type ChangeEvent, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { assetUrl, errorMessage } from '../api/client'
import { useAnalyzeClothing, useCreateClothesBulk, useRedetectClothing } from '../api/clothes'
import { Icon } from '../components/Icon'
import ItemCard from '../components/ItemCard'
import { formFromAnalysis, toCreateBody, type ItemForm } from '../components/itemForm'
import type { MultiAnalyzeResponse } from '../types/api'
import s from './pages.module.css'

const STEPS = ['촬영', '옷 찾기·배경 제거', 'AI 분석', '내 검수']

export default function AddItemPage() {
  const navigate = useNavigate()
  const analyze = useAnalyzeClothing()
  const redetect = useRedetectClothing()
  const save = useCreateClothesBulk()
  const fileRef = useRef<HTMLInputElement>(null)

  const [preview, setPreview] = useState<string | null>(null)
  const [result, setResult] = useState<MultiAnalyzeResponse | null>(null)
  const [forms, setForms] = useState<ItemForm[]>([])

  // 미리보기 URL 정리
  useEffect(
    () => () => {
      if (preview) URL.revokeObjectURL(preview)
    },
    [preview],
  )

  const applyResult = (res: MultiAnalyzeResponse) => {
    setResult(res)
    setForms(res.items.map((it) => formFromAnalysis(it.analysis)))
  }

  const pickFile = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    e.target.value = '' // 같은 사진을 다시 골라도 동작하도록
    if (!file) return
    setPreview(URL.createObjectURL(file))
    setResult(null)
    setForms([])
    analyze.mutate(file, { onSuccess: applyResult })
  }

  const retryAi = () => {
    if (result) redetect.mutate(result.original_image_url, { onSuccess: applyResult })
  }

  const busy = analyze.isPending || redetect.isPending
  const selected = result ? result.items.map((it, i) => ({ it, f: forms[i] })).filter((x) => x.f?.include) : []
  const missingName = selected.some((x) => !x.f.name.trim())
  const found = result && !result.ai_error ? result.items.length : 0
  const stepDone = result && !busy ? 4 : busy ? 1 : 0

  const submit = (e: FormEvent) => {
    e.preventDefault()
    if (!result || selected.length === 0) return
    save.mutate(
      selected.map(({ it, f }) => toCreateBody(it, f, result.original_image_url)),
      { onSuccess: () => navigate('/closet') },
    )
  }

  return (
    <form className={s.page} onSubmit={submit}>
      <div className={s.backRow}>
        <Link to="/closet" aria-label="닫기" className={s.iconLink}>
          <Icon name="close" size={22} />
        </Link>
        <h1 className={s.title} style={{ fontSize: 20 }}>
          새 옷 등록
        </h1>
      </div>

      <ol className={s.steps} aria-label="등록 단계">
        {STEPS.map((label, i) => (
          <li key={label} aria-current={i === stepDone - 1 ? 'step' : undefined}>
            <span className={`${s.stepBar} ${i < stepDone ? s.stepDone : ''} ${busy && (i === 1 || i === 2) ? s.stepActive : ''}`} />
            {label}
          </li>
        ))}
      </ol>

      <div className={s.addLayout}>
        {/* 왼쪽: 원본 사진 */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          <button
            type="button"
            className={s.dropzone}
            style={{ width: '100%' }}
            onClick={() => fileRef.current?.click()}
            disabled={busy}
            aria-label={preview ? '다른 사진 고르기' : '옷 사진 선택 또는 촬영'}
          >
            {preview || result ? (
              <img
                className={s.preview}
                src={preview ?? assetUrl(result!.original_image_url)}
                alt="올린 옷 사진"
                style={busy ? { opacity: 0.45 } : undefined}
              />
            ) : (
              <>
                <Icon name="camera" size={32} />
                <span style={{ fontSize: 15, fontWeight: 600 }}>옷 사진 선택 또는 촬영</span>
                <span style={{ fontSize: 13 }}>한 벌도, 여러 벌을 같이 찍어도 돼요</span>
              </>
            )}
            {busy && (
              <span className={s.analyzing} role="status">
                <Icon name="sparkle" size={18} /> AI가 옷을 찾고 있어요…
              </span>
            )}
          </button>
          <input ref={fileRef} type="file" accept="image/jpeg,image/png,image/webp" hidden onChange={pickFile} />
          <p className={s.subtitle} style={{ textAlign: 'center' }}>
            {result && !busy
              ? '사진을 누르면 다른 사진으로 바꿀 수 있어요.'
              : '여러 벌은 겹치지 않게 펼쳐서 찍으면 더 정확해요. jpg · png · webp, 10MB 이하'}
          </p>
        </div>

        {/* 오른쪽: 찾은 옷 검수 */}
        <section style={{ display: 'flex', flexDirection: 'column', gap: 12 }} aria-label="찾은 옷">
          {analyze.error && (
            <p className={s.notice} role="alert">
              {errorMessage(analyze.error)}
            </p>
          )}
          {redetect.error && (
            <p className={s.notice} role="alert">
              {errorMessage(redetect.error)}
            </p>
          )}
          {result?.ai_error && !busy && (
            <div className={s.notice} role="alert">
              <p>{result.ai_error} 아래에 직접 입력해도 돼요.</p>
              <button type="button" className="btn" style={{ height: 40, marginTop: 8 }} onClick={retryAi}>
                <Icon name="refresh" size={16} /> AI 다시 분석
              </button>
            </div>
          )}
          {found > 0 && !busy && (
            <p className={s.aiNotice}>
              <Icon name="sparkle" size={16} />
              {found === 1 ? '옷 1벌을 찾았어요. 다른 부분만 고쳐 주세요.' : `옷 ${found}벌을 찾았어요. 등록할 옷만 남기고 확인해 주세요.`}
            </p>
          )}
          {!result && !busy && !analyze.error && (
            <div className="card">
              <p className={s.sectionTitle}>이렇게 찍으면 좋아요</p>
              <ul className={s.tips} style={{ marginTop: 8, color: 'var(--color-text-sub)' }}>
                <li>옷을 바닥이나 침대에 펼쳐 놓고 위에서 찍어요.</li>
                <li>여러 벌이면 서로 겹치지 않게 간격을 두세요.</li>
                <li>무늬 없는 배경이면 배경이 더 깔끔하게 지워져요.</li>
              </ul>
            </div>
          )}

          {result &&
            !busy &&
            result.items.map((item, i) => (
              <ItemCard
                key={item.image_url}
                item={item}
                index={i}
                form={forms[i]}
                defaultOpen={result.items.length === 1}
                onChange={(next) => setForms((prev) => prev.map((f, j) => (j === i ? next : f)))}
              />
            ))}
        </section>
      </div>

      {save.error && <p className="error-text">{errorMessage(save.error)}</p>}
      {missingName && <p className="error-text">이름이 빈 옷이 있어요. 이름을 적거나 '등록' 체크를 빼 주세요.</p>}
      <button
        type="submit"
        className="btn btn-primary"
        style={{ height: 52 }}
        disabled={!result || busy || selected.length === 0 || missingName || save.isPending}
      >
        {save.isPending ? '저장 중…' : selected.length > 1 ? `${selected.length}벌 옷장에 저장` : '옷장에 저장'}
      </button>
    </form>
  )
}
