/**
 * 브라우저에서 옷 사진의 배경을 지운다 (@imgly/background-removal, 무료).
 *
 * 배포 서버(Vercel 무료)는 용량 제한 때문에 rembg 를 못 돌려서,
 * 서버가 배경을 못 지운 사진만 사용자 기기에서 처리한다.
 * - 라이브러리(수 MB)는 처음 쓸 때만 불러온다 (dynamic import).
 * - AI 모델은 처음 한 번 imgly CDN 에서 받아 브라우저에 캐시된다.
 * - 라이선스: AGPL-3.0 (이 프로젝트는 소스를 GitHub 에 공개하고 있음)
 */
const CONFIG = {
  model: 'isnet_quint8', // 가장 가벼운 모델 (처음 한 번 약 40MB 받은 뒤 브라우저에 캐시)
  output: { format: 'image/png' },
} as const

let preloading: Promise<void> | null = null

/**
 * 모델을 미리 받아 둔다. 사진을 고르자마자 부르면 서버가 옷을 찾는 동안
 * 다운로드가 같이 진행돼서 기다리는 시간이 줄어든다.
 * 내 PC 개발 서버(npm run dev)는 서버 rembg 가 배경을 지우므로 받지 않는다.
 */
export function preloadBackgroundRemoval(): void {
  if (!import.meta.env.PROD || preloading) return
  preloading = import('@imgly/background-removal')
    .then(({ preload }) => preload(CONFIG))
    .catch((err) => {
      console.warn('배경 제거 모델 미리 받기 실패', err)
      preloading = null
    })
}

export async function removeBackgroundInBrowser(image: Blob): Promise<Blob> {
  const { removeBackground } = await import('@imgly/background-removal')
  return removeBackground(image, CONFIG)
}
