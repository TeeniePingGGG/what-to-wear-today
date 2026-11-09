// 백엔드 app/models/enums.py · app/schemas/*.py 와 맞춰야 하는 타입

export const CATEGORIES = ['TOP', 'BOTTOM', 'OUTER', 'DRESS', 'SHOES', 'BAG', 'ACCESSORY'] as const
export type Category = (typeof CATEGORIES)[number]

export const CATEGORY_LABEL: Record<Category, string> = {
  TOP: '상의',
  BOTTOM: '하의',
  OUTER: '아우터',
  DRESS: '원피스/셋업',
  SHOES: '신발',
  BAG: '가방',
  ACCESSORY: '액세서리',
}

export const SEASONS = ['SPRING', 'SUMMER', 'FALL', 'WINTER'] as const
export type Season = (typeof SEASONS)[number]

export const SEASON_LABEL: Record<Season, string> = {
  SPRING: '봄',
  SUMMER: '여름',
  FALL: '가을',
  WINTER: '겨울',
}

export type ClothingStatus = 'ACTIVE' | 'LAUNDRY' | 'ARCHIVED'

export interface ClothingInput {
  name: string
  category: Category
  sub_category?: string | null
  color_name?: string | null
  color_hex?: string | null
  seasons: Season[]
  styles: string[]
  material?: string | null
  warmth_level: number
  is_waterproof: boolean
  memo?: string | null
}

export interface Clothing extends ClothingInput {
  id: number
  image_url: string
  original_image_url: string | null
  ai_analysis: Record<string, unknown> | null
  is_verified: boolean
  status: ClothingStatus
  wear_count: number
  last_worn_at: string | null
  created_at: string
  updated_at: string
}

export interface ClothingCreate extends ClothingInput {
  image_url: string
  original_image_url: string | null
  ai_analysis: Record<string, unknown> | null
}

export interface ClothingAnalysis {
  is_clothing: boolean
  name: string
  category: Category
  sub_category: string | null
  color_name: string | null
  color_hex: string | null
  seasons: Season[]
  styles: string[]
  material: string | null
  warmth_level: number
  is_waterproof: boolean
  /** AI가 확신하지 못한 필드 이름 (예: "material") */
  low_confidence_fields: string[]
}

export interface AnalyzedItem {
  /** 옷 한 벌만 잘라 배경을 지운 이미지 */
  image_url: string
  background_removed: boolean
  analysis: ClothingAnalysis | null
  ai_raw: Record<string, unknown> | null
}

export interface MultiAnalyzeResponse {
  original_image_url: string
  /** 찾은 옷들. AI 실패 시 사진 전체 1장 */
  items: AnalyzedItem[]
  ai_error: string | null
}

export interface ReanalyzeResponse {
  analysis: ClothingAnalysis | null
  ai_raw: Record<string, unknown> | null
  ai_error: string | null
}

export interface User {
  id: number
  email: string
  nickname: string
  default_location_name: string | null
  created_at: string
}

export interface TokenResponse {
  access_token: string
  token_type: 'bearer'
}
