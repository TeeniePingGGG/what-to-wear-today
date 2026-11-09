"""Vision AI(Gemini)로 옷 사진에서 메타데이터를 뽑는다 (계획서 기능 1).

- detect_clothes   : 사진 속 옷을 전부 찾아 위치(box_2d)와 정보를 돌려준다 (여러 벌 한 번에 등록)
- analyze_clothing : 잘라낸 옷 한 벌만 다시 분석한다 ('AI 다시 분석')

Gemini 의 구조화 출력(response_schema)으로 정해진 JSON 형식만 받는다.
"""

from google.genai import types

from app.schemas.clothing import ClothingAnalysis, DetectionResult
from app.services.gemini import AIError, generate

VisionError = AIError  # 기존 코드 호환용 이름

FIELD_RULES = """- name: 한국어로 짧게, "색상 + 종류" (예: "네이비 라운드넥 니트", "연청 와이드 데님").
- category: TOP(상의) BOTTOM(하의) OUTER(아우터) DRESS(원피스·점프수트·셋업) SHOES(신발) BAG(가방) ACCESSORY(모자·머플러·벨트 등) 중 하나.
- sub_category: 한국어 세부 종류 (예: 셔츠, 맨투맨, 후드티, 슬랙스, 트렌치코트, 스니커즈).
- color_name: 한국어 대표 색 이름 하나 (예: 네이비, 아이보리, 차콜, 카멜, 연청).
- color_hex: 대표 색의 #RRGGBB.
- seasons: 입기 좋은 계절 SPRING SUMMER FALL WINTER (여러 개 가능).
- styles: 1~3개. 가능하면 [미니멀, 캐주얼, 포멀, 스트릿, 스포티, 빈티지, 러블리, 아메카지, 댄디] 중에서.
- material: 보이는 대로 추정한 소재 (예: 면, 울 혼방, 데님, 가죽, 나일론). 모르면 null.
- warmth_level: 보온성 1(매우 얇음, 반팔·린넨) ~ 5(매우 두꺼움, 패딩).
- is_waterproof: 방수·생활방수로 보이면 true (트렌치코트, 바람막이, 고무 소재 등).
- low_confidence_fields: 사진만으로 확신하기 어려운 필드 이름 목록 (예: ["material", "warmth_level"])."""

DETECT_PROMPT = f"""너는 패션 스타일리스트 앱의 옷장 등록 도우미야.
사진 속에 있는 옷·신발·가방·액세서리를 전부 찾아서, 한 벌마다 items 에 하나씩 넣어 정해진 JSON 형식으로만 답해.

규칙
- 한 켤레의 신발, 한 벌의 셋업처럼 같이 쓰는 것은 하나로 쳐.
- 사람이 입고 있는 옷도 각각 찾아. 단 너무 작게 보이거나 대부분 가려진 것은 빼.
- 최대 10개. 옷이 하나도 없으면 items 를 빈 배열로.
- is_clothing: 항상 true.
- box_2d: 그 옷 하나를 감싸는 사각형 [ymin, xmin, ymax, xmax]. 사진 왼쪽 위가 0, 오른쪽 아래가 1000 인 정수 좌표.
{FIELD_RULES}
"""

SINGLE_PROMPT = f"""너는 패션 스타일리스트 앱의 옷장 등록 도우미야.
사진 속 옷 한 벌을 분석해서 정해진 JSON 형식으로만 답해.

규칙
- 사진에 옷·신발·가방·액세서리가 없으면 is_clothing=false 로 하고 나머지는 대충 채워.
- 여러 벌이 보이면 가장 크게, 가운데에 보이는 한 벌만 분석해.
{FIELD_RULES}
"""


def _image(jpeg: bytes) -> types.Part:
    return types.Part.from_bytes(data=jpeg, mime_type="image/jpeg")


def detect_clothes(jpeg: bytes) -> tuple[DetectionResult, str]:
    """사진 속 옷을 전부 찾는다. (결과, 사용한 모델)"""
    return generate([_image(jpeg), DETECT_PROMPT], DetectionResult)


def analyze_clothing(jpeg: bytes) -> tuple[ClothingAnalysis, dict]:
    """옷 한 벌 분석. (결과, DB 저장용 원본 JSON)"""
    analysis, model = generate([_image(jpeg), SINGLE_PROMPT], ClothingAnalysis)
    return analysis, {"model": model, "result": analysis.model_dump(mode="json")}
