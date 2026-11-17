import { useSearchParams } from 'react-router-dom'

/**
 * 코디를 볼 날: 오늘 또는 내일.
 * 전날 밤에 내일 코디를 미리 받아 두고, 다음 날 아침엔 '오늘'에서 바로 볼 수 있다.
 * 주소의 ?day=tomorrow 로 기억해서 오늘 화면 ↔ 조건 입력 화면을 오가도 유지된다.
 */
export type PlanDay = 'today' | 'tomorrow'

export const PLAN_DAY_LABEL: Record<PlanDay, string> = { today: '오늘', tomorrow: '내일' }

const KST = 'Asia/Seoul'
const DAY_MS = 24 * 60 * 60 * 1000

/** 한국 시간 기준 날짜 "YYYY-MM-DD" (백엔드 target_date 와 같은 형식) */
export function planDate(day: PlanDay): string {
  const base = Date.now() + (day === 'tomorrow' ? DAY_MS : 0)
  return new Intl.DateTimeFormat('sv-SE', { timeZone: KST }).format(base) // sv-SE 는 YYYY-MM-DD 형식
}

/** 화면 표시용: "11월 18일 수요일" */
export function planDateLabel(day: PlanDay): string {
  const base = Date.now() + (day === 'tomorrow' ? DAY_MS : 0)
  return new Intl.DateTimeFormat('ko-KR', { timeZone: KST, month: 'long', day: 'numeric', weekday: 'long' }).format(base)
}

export function usePlanDay(): [PlanDay, (day: PlanDay) => void] {
  const [params, setParams] = useSearchParams()
  const day: PlanDay = params.get('day') === 'tomorrow' ? 'tomorrow' : 'today'
  const setDay = (next: PlanDay) =>
    setParams(
      (prev) => {
        const p = new URLSearchParams(prev)
        if (next === 'tomorrow') p.set('day', 'tomorrow')
        else p.delete('day')
        return p
      },
      { replace: true },
    )
  return [day, setDay]
}

/** 같은 날을 유지하며 다른 화면으로 갈 때 붙이는 주소 꼬리 */
export const daySuffix = (day: PlanDay) => (day === 'tomorrow' ? '?day=tomorrow' : '')
