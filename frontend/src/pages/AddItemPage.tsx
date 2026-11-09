import { useEffect, useRef, useState, type ChangeEvent, type FormEvent, type ReactNode } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { assetUrl, errorMessage } from '../api/client'
import { useAnalyzeClothing, useCreateClothing, useReanalyzeClothing } from '../api/clothes'
import { Icon } from '../components/Icon'
import {
  CATEGORIES,
  CATEGORY_LABEL,
  SEASONS,
  SEASON_LABEL,
  type AnalyzeResponse,
  type Category,
  type ClothingAnalysis,
  type Season,
} from '../types/api'
import s from './pages.module.css'

const STEPS = ['촬영', '배경 제거', 'AI 분석', '내 검수']

interface FormState {
  name: string
  category: Category
  subCategory: string
  colorName: string
  colorHex: string
  seasons: Season[]
  styles: string
  material: string
  warmth: number
  waterproof: boolean
}

const EMPTY_FORM: FormState = {
  name: '',
  category: 'TOP',
  subCategory: '',
  colorName: '',
  colorHex: '#2C3A57',
  seasons: [],
  styles: '',
  material: '',
  warmth: 3,
  waterproof: false,
}

function fromAnalysis(a: ClothingAnalysis): FormState {
  return {
    name: a.name,
    category: a.category,
    subCategory: a.sub_category ?? '',
    colorName: a.color_name ?? '',
    colorHex: a.color_hex ?? EMPTY_FORM.colorHex,
    seasons: a.seasons,
    styles: a.styles.join(', '),
    material: a.material ?? '',
    warmth: a.warmth_level,
    waterproof: a.is_waterproof,
  }
}

export default function AddItemPage() {
  const navigate = useNavigate()
  const analyze = useAnalyzeClothing()
  const reanalyze = useReanalyzeClothing()
  const create = useCreateClothing()
  const fileRef = useRef<HTMLInputElement>(null)

  const [preview, setPreview] = useState<string | null>(null)
  const [result, setResult] = useState<AnalyzeResponse | null>(null)
  const [form, setForm] = useState<FormState>(EMPTY_FORM)

  // 미리보기 URL 정리
  useEffect(
    () => () => {
      if (preview) URL.revokeObjectURL(preview)
    },
    [preview],
  )

  const set = <K extends keyof FormState>(key: K, value: FormState[K]) => setForm((f) => ({ ...f, [key]: value }))

  const pickFile = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    e.target.value = '' // 같은 사진을 다시 골라도 동작하도록
    if (!file) return
    setPreview(URL.createObjectURL(file))
    setResult(null)
    setForm(EMPTY_FORM)
    analyze.mutate(file, {
      onSuccess: (res) => {
        setResult(res)
        if (res.analysis?.is_clothing) setForm(fromAnalysis(res.analysis))
      },
    })
  }

  const retryAi = () => {
    if (!result) return
    reanalyze.mutate(result.image_url, {
      onSuccess: (res) => {
        setResult({ ...result, ...res })
        if (res.analysis?.is_clothing) setForm(fromAnalysis(res.analysis))
      },
    })
  }

  const lowConfidence = new Set(result?.analysis?.is_clothing ? result.analysis.low_confidence_fields : [])
  const check = (field: string): ReactNode =>
    lowConfidence.has(field) ? <span className={s.checkBadge}>확인 필요</span> : null

  const stepDone = result ? 4 : analyze.isPending ? 1 : 0

  const submit = (e: FormEvent) => {
    e.preventDefault()
    if (!result) return
    create.mutate(
      {
        image_url: result.image_url,
        original_image_url: result.original_image_url,
        ai_analysis: result.ai_raw,
        name: form.name,
        category: form.category,
        sub_category: form.subCategory || null,
        color_name: form.colorName || null,
        color_hex: form.colorHex.toUpperCase(),
        seasons: form.seasons,
        styles: form.styles
          .split(',')
          .map((x) => x.trim())
          .filter(Boolean),
        material: form.material || null,
        warmth_level: form.warmth,
        is_waterproof: form.waterproof,
      },
      { onSuccess: () => navigate('/closet') },
    )
  }

  const shownImage = result ? assetUrl(result.image_url) : preview

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
            <span
              className={`${s.stepBar} ${i < stepDone ? s.stepDone : ''} ${
                analyze.isPending && (i === 1 || i === 2) ? s.stepActive : ''
              }`}
            />
            {label}
          </li>
        ))}
      </ol>

      <div className={s.addLayout}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          <button
            type="button"
            className={`${s.dropzone} ${result?.background_removed ? s.checker : ''}`}
            style={{ width: '100%' }}
            onClick={() => fileRef.current?.click()}
            disabled={analyze.isPending}
            aria-label={shownImage ? '다른 사진 고르기' : '옷 사진 선택 또는 촬영'}
          >
            {shownImage ? (
              <img
                className={s.preview}
                src={shownImage}
                alt={result?.background_removed ? '배경을 지운 옷 사진' : '선택한 옷 사진'}
                style={analyze.isPending ? { opacity: 0.45 } : undefined}
              />
            ) : (
              <>
                <Icon name="camera" size={32} />
                <span style={{ fontSize: 15, fontWeight: 600 }}>옷 사진 선택 또는 촬영</span>
                <span style={{ fontSize: 13 }}>jpg · png · webp, 10MB 이하</span>
              </>
            )}
            {analyze.isPending && (
              <span className={s.analyzing} role="status">
                <Icon name="sparkle" size={18} /> 배경을 지우고 AI가 분석하고 있어요…
              </span>
            )}
          </button>
          <input
            ref={fileRef}
            type="file"
            accept="image/jpeg,image/png,image/webp"
            hidden
            onChange={pickFile}
          />
          {analyze.isPending && (
            <p className={s.subtitle} style={{ textAlign: 'center' }}>
              보통 10초 안팎 걸려요. 서버를 켠 뒤 첫 등록은 배경 제거 모델을 받느라 1분쯤 걸릴 수 있어요.
            </p>
          )}
          {result && (
            <p className={s.subtitle} style={{ textAlign: 'center' }}>
              {result.background_removed ? '배경을 지웠어요. ' : '배경 제거 없이 원본으로 등록해요. '}
              사진을 누르면 다시 고를 수 있어요.
            </p>
          )}
        </div>

        <section className="card" style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          {analyze.error && (
            <p className={s.notice} role="alert">
              {errorMessage(analyze.error)}
            </p>
          )}
          {result?.ai_error && (
            <div className={s.notice} role="alert">
              <p>{reanalyze.isPending ? 'AI가 다시 분석하고 있어요…' : `${result.ai_error} 직접 입력해도 돼요.`}</p>
              <button type="button" className="btn" style={{ height: 40, marginTop: 8 }} onClick={retryAi} disabled={reanalyze.isPending}>
                <Icon name="refresh" size={16} /> AI 다시 분석
              </button>
            </div>
          )}
          {reanalyze.error && <p className="error-text">{errorMessage(reanalyze.error)}</p>}
          {result?.analysis?.is_clothing && (
            <p className={s.aiNotice}>
              <Icon name="sparkle" size={16} /> AI가 채운 값이에요. 다른 부분만 고쳐 주세요.
            </p>
          )}
          {!result && !analyze.isPending && !analyze.error && (
            <p className={s.subtitle} style={{ marginTop: 0 }}>
              사진을 올리면 AI가 아래 정보를 자동으로 채워 줘요.
            </p>
          )}

          <fieldset disabled={!result || reanalyze.isPending} className={s.formGrid} style={{ border: 'none', padding: 0, margin: 0 }}>
            <label className={`field ${s.span2}`}>
              <span>이름 {check('name')}</span>
              <input required maxLength={100} value={form.name} onChange={(e) => set('name', e.target.value)} placeholder="예: 네이비 니트" />
            </label>
            <label className="field">
              <span>종류 {check('category')}</span>
              <select value={form.category} onChange={(e) => set('category', e.target.value as Category)}>
                {CATEGORIES.map((c) => (
                  <option key={c} value={c}>
                    {CATEGORY_LABEL[c]}
                  </option>
                ))}
              </select>
            </label>
            <label className="field">
              <span>세부 카테고리 {check('sub_category')}</span>
              <input maxLength={50} value={form.subCategory} onChange={(e) => set('subCategory', e.target.value)} placeholder="예: 라운드넥 니트" />
            </label>
            <label className="field">
              <span>색상 이름 {check('color_name')}</span>
              <input maxLength={30} value={form.colorName} onChange={(e) => set('colorName', e.target.value)} placeholder="예: 네이비" />
            </label>
            <label className="field">
              <span>대표 색 {check('color_hex')}</span>
              <input type="color" value={form.colorHex} onChange={(e) => set('colorHex', e.target.value)} style={{ padding: 4 }} />
            </label>
            <fieldset className={`field ${s.span2}`} style={{ border: 'none', padding: 0, margin: 0 }}>
              <legend style={{ marginBottom: 6 }}>계절 {check('seasons')}</legend>
              <div className={s.chipRow}>
                {SEASONS.map((v) => (
                  <button
                    key={v}
                    type="button"
                    className="chip"
                    aria-pressed={form.seasons.includes(v)}
                    onClick={() =>
                      set('seasons', form.seasons.includes(v) ? form.seasons.filter((x) => x !== v) : [...form.seasons, v])
                    }
                  >
                    {SEASON_LABEL[v]}
                  </button>
                ))}
              </div>
            </fieldset>
            <label className="field">
              <span>스타일 (쉼표로 구분) {check('styles')}</span>
              <input value={form.styles} onChange={(e) => set('styles', e.target.value)} placeholder="예: 미니멀, 캐주얼" />
            </label>
            <label className="field">
              <span>소재 {check('material')}</span>
              <input maxLength={50} value={form.material} onChange={(e) => set('material', e.target.value)} placeholder="예: 울 혼방" />
            </label>
            <label className="field">
              <span>
                보온성 {form.warmth} / 5 {check('warmth_level')}
              </span>
              <input type="range" min={1} max={5} value={form.warmth} onChange={(e) => set('warmth', Number(e.target.value))} style={{ padding: 0 }} />
            </label>
            <label className={s.checkRow}>
              <input type="checkbox" checked={form.waterproof} onChange={(e) => set('waterproof', e.target.checked)} />
              생활 방수 {check('is_waterproof')}
            </label>
          </fieldset>
        </section>
      </div>

      {create.error && <p className="error-text">{errorMessage(create.error)}</p>}
      <button type="submit" className="btn btn-primary" style={{ height: 52 }} disabled={!result || !form.name || create.isPending}>
        {create.isPending ? '저장 중…' : '옷장에 저장'}
      </button>
    </form>
  )
}
