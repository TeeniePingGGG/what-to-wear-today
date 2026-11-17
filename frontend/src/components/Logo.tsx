type Props = {
  size?: number
  className?: string
}

/** 앱 로고: 물음표 모양 옷걸이 + 해 */
export function Logo({ size = 32, className }: Props) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 64 64"
      className={className}
      role="img"
      aria-label="오늘 뭐 입지? 로고"
    >
      <rect width="64" height="64" rx="16" fill="#0b6b5d" />
      <path
        d="M26 18a6 6 0 1 1 9 5.2c-2 1.2-3 2.3-3 4.3L49 42H15l17-14.5"
        fill="none"
        stroke="#fff"
        strokeWidth={size < 40 ? 4.5 : 3.6}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <circle cx="32" cy="49" r={size < 40 ? 3.2 : 2.6} fill="#f6c453" />
    </svg>
  )
}
