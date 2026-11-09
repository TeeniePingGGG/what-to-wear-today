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

// --- 기능 2: 날씨·일정·코디 추천 ---

export type Mood = 'COMFY' | 'NEAT' | 'DRESSY'

export const MOOD_LABEL: Record<Mood, string> = {
  COMFY: '편하게',
  NEAT: '단정하게',
  DRESSY: '꾸민 듯',
}

export interface HourlyWeather {
  hour: number
  temp: number
  feels_like: number
  pop: number
  sky: string
}

export interface Weather {
  location_name: string | null
  latitude: number
  longitude: number
  temp: number
  feels_like: number
  sky: string
  /** 예: "맑음, 15시부터 비 소식" */
  summary: string
  temp_max: number
  temp_min: number
  temp_range: number
  /** 오늘 하루 최고 강수확률 (지난 시간 포함) */
  pop_max: number
  /** 지금부터 남은 시간의 최고 강수확률 */
  pop_rest: number
  rain_from: number | null
  rain_until: number | null
  hourly: HourlyWeather[]
  fetched_at: string
}

export interface Schedule {
  id: number
  date: string
  title: string
  /** "14:00:00" */
  start_time: string | null
  end_time: string | null
  location: string | null
  is_outdoor: boolean | null
  is_important: boolean
  source: 'MANUAL' | 'GOOGLE'
}

export interface ScheduleCreate {
  title: string
  start_time?: string | null
  is_important?: boolean
  is_outdoor?: boolean | null
}

export interface OutfitClothing {
  id: number
  name: string
  category: Category
  sub_category: string | null
  color_name: string | null
  color_hex: string | null
  image_url: string
}

export interface Outfit {
  id: number
  rank: number
  summary: string | null
  reasons: unknown[] | null
  tips: string[] | null
  is_selected: boolean
  items: { slot: Category; clothing_item: OutfitClothing }[]
}

export interface Recommendation {
  id: number
  target_date: string
  location_name: string | null
  weather: Weather
  situations: string[]
  mood: Mood | null
  user_note: string | null
  status: 'PENDING' | 'COMPLETED' | 'FAILED'
  created_at: string
  outfits: Outfit[]
}

export interface RecommendRequest {
  latitude: number
  longitude: number
  location_name: string | null
  situations: string[]
  mood: Mood | null
  user_note: string | null
}
