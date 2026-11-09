import type { AnalyzedItem, Category, ClothingAnalysis, ClothingCreate, Season } from '../types/api'

/** 검수 화면에서 옷 한 벌을 편집하는 값 */
export interface ItemForm {
  include: boolean
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

export function formFromAnalysis(a: ClothingAnalysis | null): ItemForm {
  return {
    include: true,
    name: a?.name ?? '',
    category: a?.category ?? 'TOP',
    subCategory: a?.sub_category ?? '',
    colorName: a?.color_name ?? '',
    colorHex: a?.color_hex ?? '#2C3A57',
    seasons: a?.seasons ?? [],
    styles: a?.styles.join(', ') ?? '',
    material: a?.material ?? '',
    warmth: a?.warmth_level ?? 3,
    waterproof: a?.is_waterproof ?? false,
  }
}

export function toCreateBody(item: AnalyzedItem, f: ItemForm, originalImageUrl: string): ClothingCreate {
  return {
    image_url: item.image_url,
    original_image_url: originalImageUrl,
    ai_analysis: item.ai_raw,
    name: f.name.trim(),
    category: f.category,
    sub_category: f.subCategory || null,
    color_name: f.colorName || null,
    color_hex: f.colorHex.toUpperCase(),
    seasons: f.seasons,
    styles: f.styles
      .split(',')
      .map((x) => x.trim())
      .filter(Boolean),
    material: f.material || null,
    warmth_level: f.warmth,
    is_waterproof: f.waterproof,
  }
}
