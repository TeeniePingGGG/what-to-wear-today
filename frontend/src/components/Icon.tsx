// 선(stroke) 아이콘 모음 — 색은 currentColor 를 따름
const PATHS = {
  home: <path d="M3 10l9-7 9 7v10a2 2 0 0 1-2 2h-4v-7H9v7H5a2 2 0 0 1-2-2z" />,
  closet: (
    <>
      <path d="M12 6a2 2 0 1 1 2 2c-1 0-2 .7-2 2v1" />
      <path d="M12 11L3 17.5A1.5 1.5 0 0 0 4 20h16a1.5 1.5 0 0 0 1-2.5z" />
    </>
  ),
  plus: <path d="M12 5v14M5 12h14" />,
  plusSquare: (
    <>
      <rect x="3" y="3" width="18" height="18" rx="5" />
      <path d="M12 8v8M8 12h8" />
    </>
  ),
  user: (
    <>
      <circle cx="12" cy="8" r="4" />
      <path d="M4 21a8 8 0 0 1 16 0" />
    </>
  ),
  calendar: (
    <>
      <rect x="3" y="4" width="18" height="18" rx="2" />
      <path d="M16 2v4M8 2v4M3 10h18" />
    </>
  ),
  chevronRight: <path d="M9 18l6-6-6-6" />,
  chevronLeft: <path d="M15 18l-6-6 6-6" />,
  sparkle: <path d="M12 3l1.9 5.1L19 10l-5.1 1.9L12 17l-1.9-5.1L5 10l5.1-1.9z" />,
  refresh: (
    <>
      <path d="M21 12a9 9 0 1 1-3-6.7L21 8" />
      <path d="M21 3v5h-5" />
    </>
  ),
  camera: (
    <>
      <path d="M3 8a2 2 0 0 1 2-2h2l2-3h6l2 3h2a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
      <circle cx="12" cy="13" r="4" />
    </>
  ),
  search: (
    <>
      <circle cx="11" cy="11" r="7" />
      <path d="M20 20l-3.5-3.5" />
    </>
  ),
  close: <path d="M6 6l12 12M18 6L6 18" />,
  logout: (
    <>
      <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
      <path d="M16 17l5-5-5-5M21 12H9" />
    </>
  ),
} as const

export type IconName = keyof typeof PATHS

export function Icon({ name, size = 20, strokeWidth = 1.9 }: { name: IconName; size?: number; strokeWidth?: number }) {
  return (
    <svg
      aria-hidden="true"
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={strokeWidth}
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      {PATHS[name]}
    </svg>
  )
}
