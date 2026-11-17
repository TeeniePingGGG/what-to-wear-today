/**
 * 업로드 전에 사진을 줄인다.
 * - 휴대폰 사진은 5~10MB 라서 그대로 보내면 느리고, Vercel 서버는 4.5MB 넘는 요청을 받지 못한다.
 * - 서버도 어차피 긴 변 1280px 로 줄여서 쓰므로 화질 손해는 거의 없다.
 */
const MAX_SIDE = 1600
const QUALITY = 0.85

export async function shrinkImage(file: File): Promise<File> {
  if (file.size < 1.5 * 1024 * 1024) return file // 이미 작으면 그대로

  let bitmap: ImageBitmap
  try {
    bitmap = await createImageBitmap(file, { imageOrientation: 'from-image' }) // 휴대폰 회전 정보 반영
  } catch {
    return file // 브라우저가 못 여는 형식이면 서버에 맡김
  }

  const scale = Math.min(1, MAX_SIDE / Math.max(bitmap.width, bitmap.height))
  const canvas = document.createElement('canvas')
  canvas.width = Math.round(bitmap.width * scale)
  canvas.height = Math.round(bitmap.height * scale)
  canvas.getContext('2d')?.drawImage(bitmap, 0, 0, canvas.width, canvas.height)
  bitmap.close()

  const blob = await new Promise<Blob | null>((resolve) => canvas.toBlob(resolve, 'image/jpeg', QUALITY))
  if (!blob || blob.size >= file.size) return file
  return new File([blob], file.name.replace(/\.\w+$/, '') + '.jpg', { type: 'image/jpeg' })
}
