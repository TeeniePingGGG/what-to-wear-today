import { useId, useState, type ReactNode } from 'react'
import { assetUrl } from '../api/client'
import { CATEGORIES, CATEGORY_LABEL, SEASONS, SEASON_LABEL, type AnalyzedItem, type Category } from '../types/api'
import { Icon } from './Icon'
import c from './ItemCard.module.css'
import type { ItemForm } from './itemForm'

interface Props {
  item: AnalyzedItem
  form: ItemForm
  onChange: (next: ItemForm) => void
  index: number
  defaultOpen?: boolean
}

export default function ItemCard({ item, form, onChange, index, defaultOpen = false }: Props) {
  const [open, setOpen] = useState(defaultOpen)
  const detailsId = useId()
  const low = new Set(item.analysis?.low_confidence_fields ?? [])
  const lowCount = [...low].filter((f) => !['name', 'category'].includes(f)).length

  const set = <K extends keyof ItemForm>(key: K, value: ItemForm[K]) => onChange({ ...form, [key]: value })
  const check = (field: string): ReactNode => (low.has(field) ? <span className={c.badge}>확인 필요</span> : null)
  const label = form.name || `${index + 1}번째 옷`

  return (
    <article className={`${c.card} ${form.include ? '' : c.excluded}`} aria-label={label}>
      <div className={c.top}>
        <div className={`${c.thumb} ${item.background_removed ? c.checker : ''}`}>
          <img src={assetUrl(item.image_url)} alt={label} />
        </div>

        <div className={c.main}>
          <label className={c.inlineField}>
            <span className="visually-hidden">이름 {low.has('name') && '(확인 필요)'}</span>
            <input
              required={form.include}
              maxLength={100}
              value={form.name}
              disabled={!form.include}
              onChange={(e) => set('name', e.target.value)}
              placeholder="이름 (예: 네이비 니트)"
              className={c.nameInput}
            />
          </label>
          <div className={c.row}>
            <label className={c.inlineField}>
              <span className="visually-hidden">종류</span>
              <select value={form.category} disabled={!form.include} onChange={(e) => set('category', e.target.value as Category)}>
                {CATEGORIES.map((cat) => (
                  <option key={cat} value={cat}>
                    {CATEGORY_LABEL[cat]}
                  </option>
                ))}
              </select>
            </label>
            <span className={c.swatch} style={{ background: form.colorHex }} aria-hidden="true" />
            <span className={c.meta}>{[form.colorName, form.seasons.map((x) => SEASON_LABEL[x]).join('/')].filter(Boolean).join(' · ')}</span>
          </div>
        </div>

        <label className={c.include}>
          <input type="checkbox" checked={form.include} onChange={(e) => set('include', e.target.checked)} />
          <span>등록</span>
        </label>
      </div>

      {form.include && (
        <>
          <button type="button" className={c.toggle} aria-expanded={open} aria-controls={detailsId} onClick={() => setOpen(!open)}>
            세부 정보 {open ? '접기' : '수정'}
            {lowCount > 0 && !open && <span className={c.badge}>확인 필요 {lowCount}</span>}
            <span className={c.chevron} data-open={open}>
              <Icon name="chevronRight" size={16} />
            </span>
          </button>

          {open && (
            <div id={detailsId} className={c.details}>
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
              <label className="field">
                <span>소재 {check('material')}</span>
                <input maxLength={50} value={form.material} onChange={(e) => set('material', e.target.value)} placeholder="예: 울 혼방" />
              </label>
              <fieldset className={`field ${c.span2}`} style={{ border: 'none', padding: 0, margin: 0 }}>
                <legend style={{ marginBottom: 6 }}>계절 {check('seasons')}</legend>
                <div className={c.chips}>
                  {SEASONS.map((v) => (
                    <button
                      key={v}
                      type="button"
                      className="chip"
                      aria-pressed={form.seasons.includes(v)}
                      onClick={() => set('seasons', form.seasons.includes(v) ? form.seasons.filter((x) => x !== v) : [...form.seasons, v])}
                    >
                      {SEASON_LABEL[v]}
                    </button>
                  ))}
                </div>
              </fieldset>
              <label className={`field ${c.span2}`}>
                <span>스타일 (쉼표로 구분) {check('styles')}</span>
                <input value={form.styles} onChange={(e) => set('styles', e.target.value)} placeholder="예: 미니멀, 캐주얼" />
              </label>
              <label className="field">
                <span>
                  보온성 {form.warmth} / 5 {check('warmth_level')}
                </span>
                <input type="range" min={1} max={5} value={form.warmth} onChange={(e) => set('warmth', Number(e.target.value))} style={{ padding: 0 }} />
              </label>
              <label className={c.checkRow}>
                <input type="checkbox" checked={form.waterproof} onChange={(e) => set('waterproof', e.target.checked)} />
                생활 방수 {check('is_waterproof')}
              </label>
            </div>
          )}
        </>
      )}
    </article>
  )
}
