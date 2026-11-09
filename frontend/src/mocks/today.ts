// 스타일리스트 가이드 화면용 샘플 데이터 (기능 3 개발 시 삭제)

export const sampleOutfit = {
  id: 1,
  summary:
    '오후 비 예보에 맞춰 트렌치코트와 가죽 더비슈즈를 골랐어요. 발표가 있어 셔츠와 슬랙스로 단정함을 챙겼어요.',
  items: [
    { name: '옥스퍼드 셔츠', sub: '상의 · 아이보리', color: '#EFE8D8', shape: 'top' },
    { name: '울 슬랙스', sub: '하의 · 차콜', color: '#4A4E55', shape: 'pants' },
    { name: '트렌치코트', sub: '아우터 · 카멜', color: '#B98A55', shape: 'coat' },
    { name: '더비 슈즈', sub: '신발 · 블랙', color: '#26282C', shape: 'shoe' },
  ] as const,
  reasons: [
    { tag: '기온', tone: 'warm', title: '일교차 9° — 레이어드', body: '아침 9°, 낮 18°라 셔츠 위에 코트를 걸치고, 더우면 벗을 수 있게 했어요.' },
    { tag: '비', tone: 'rain', title: '15시부터 강수 60%', body: '생활 방수 트렌치코트와 가죽 더비슈즈라 젖어도 금방 닦여요.' },
    { tag: '일정', tone: 'primary', title: '발표 → 저녁 약속', body: '아이보리·차콜·카멜 톤으로 발표엔 단정하게, 코트를 벗으면 저녁엔 편하게.' },
  ] as const,
  tips: [
    '셔츠 소매를 한 번 접어 올리면 발표 때 손동작이 한결 가벼워 보여요.',
    '트렌치코트 벨트는 앞에서 묶지 말고 뒤로 느슨하게 묶어 주세요.',
    '슬랙스와 비슷한 차콜 양말로 다리 라인을 길게 이어 보세요.',
  ],
}
