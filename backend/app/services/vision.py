"""Vision AI(Gemini)로 옷 사진에서 메타데이터를 뽑는다 (계획서 기능 1).

Gemini 의 구조화 출력(response_schema)을 써서 ClothingAnalysis 형식의 JSON 만 받는다.
"""

import logging
import time

import httpx

from google import genai
from google.genai import errors as genai_errors
from google.genai import types
from pydantic import ValidationError

from app.core.config import settings
from app.schemas.clothing import ClothingAnalysis

log = logging.getLogger(__name__)

PROMPT = """너는 패션 스타일리스트 앱의 옷장 등록 도우미야.
사진 속 옷 한 벌을 분석해서 정해진 JSON 형식으로만 답해.

규칙
- 사진에 옷·신발·가방·액세서리가 없으면 is_clothing=false 로 하고 나머지는 대충 채워.
- 여러 벌이 보이면 가장 크게, 가운데에 보이는 한 벌만 분석해.
- name: 한국어로 짧게, "색상 + 종류" (예: "네이비 라운드넥 니트", "연청 와이드 데님").
- category: TOP(상의) BOTTOM(하의) OUTER(아우터) DRESS(원피스·점프수트·셋업) SHOES(신발) BAG(가방) ACCESSORY(모자·머플러·벨트 등) 중 하나.
- sub_category: 한국어 세부 종류 (예: 셔츠, 맨투맨, 후드티, 슬랙스, 트렌치코트, 스니커즈).
- color_name: 한국어 대표 색 이름 하나 (예: 네이비, 아이보리, 차콜, 카멜, 연청).
- color_hex: 대표 색의 #RRGGBB.
- seasons: 입기 좋은 계절 SPRING SUMMER FALL WINTER (여러 개 가능).
- styles: 1~3개. 가능하면 [미니멀, 캐주얼, 포멀, 스트릿, 스포티, 빈티지, 러블리, 아메카지, 댄디] 중에서.
- material: 보이는 대로 추정한 소재 (예: 면, 울 혼방, 데님, 가죽, 나일론). 모르면 null.
- warmth_level: 보온성 1(매우 얇음, 반팔·린넨) ~ 5(매우 두꺼움, 패딩).
- is_waterproof: 방수·생활방수로 보이면 true (트렌치코트, 바람막이, 고무 소재 등).
- low_confidence_fields: 사진만으로 확신하기 어려운 필드 이름 목록 (예: ["material", "warmth_level"]).
"""


class VisionError(Exception):
    """사용자에게 보여 줄 메시지를 담은 분석 실패."""


_client: genai.Client | None = None


def _get_client() -> genai.Client:
    global _client
    if not settings.gemini_api_key:
        raise VisionError("AI 키가 설정되지 않았어요. backend/.env 의 GEMINI_API_KEY 를 확인해 주세요.")
    if _client is None:
        _client = genai.Client(
            api_key=settings.gemini_api_key,
            http_options=types.HttpOptions(timeout=REQUEST_TIMEOUT_S * 1000),  # 응답이 없으면 끊기
        )
    return _client


RETRY_DELAYS = (2,)  # 서버 혼잡(5xx) 시 같은 모델로 재시도하기 전 대기 시간(초)
REQUEST_TIMEOUT_S = 25  # 요청 1번의 최대 대기 시간
TOTAL_BUDGET_S = 60  # 재시도·예비 모델 포함 전체 최대 시간


def _models() -> list[str]:
    models = [settings.gemini_model]
    if settings.gemini_fallback_model and settings.gemini_fallback_model not in models:
        models.append(settings.gemini_fallback_model)
    return models


_no_thinking_config: set[str] = set()  # thinking_level 을 지원하지 않는 모델 (한 번 거절되면 기억)


def _call(client: genai.Client, model: str, jpeg: bytes) -> types.GenerateContentResponse:
    # 옷 분류는 깊게 '생각'할 필요가 없어서 thinking 을 최소로 줄여 응답을 빠르게 한다
    thinking = None
    if settings.gemini_thinking and model not in _no_thinking_config:
        thinking = types.ThinkingConfig(thinking_level=settings.gemini_thinking.upper())
    return client.models.generate_content(
        model=model,
        contents=[types.Part.from_bytes(data=jpeg, mime_type="image/jpeg"), PROMPT],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=ClothingAnalysis,
            temperature=0.2,
            thinking_config=thinking,
        ),
    )


def analyze_clothing(jpeg: bytes) -> tuple[ClothingAnalysis, dict]:
    """(검증된 분석 결과, DB 저장용 원본 JSON) 을 돌려준다.

    서버 혼잡(503 등)이면 잠깐 쉬고 재시도하고, 그래도 안 되면 예비 모델(GEMINI_FALLBACK_MODEL)로 바꿔 시도한다.
    """
    client = _get_client()
    last_error: VisionError | None = None
    started = time.monotonic()
    busy = VisionError("AI 서버가 지금 붐벼요. 잠시 후 'AI 다시 분석'을 눌러 주세요.")

    for model in _models():
        for attempt in range(len(RETRY_DELAYS) + 1):
            if time.monotonic() - started > TOTAL_BUDGET_S:
                log.warning("Gemini 분석 시간 초과 (%ds) — 중단", TOTAL_BUDGET_S)
                raise last_error or busy
            try:
                response = _call(client, model, jpeg)
            except genai_errors.ClientError as e:
                if e.code == 400 and "think" in str(e).lower() and model not in _no_thinking_config:
                    log.info("%s 는 thinking 설정을 지원하지 않아 기본값으로 다시 요청", model)
                    _no_thinking_config.add(model)
                    continue
                log.warning("Gemini 요청 오류 (%s): %s", model, e)
                if e.code in (400, 401, 403) and "API key" in str(e):
                    raise VisionError("AI 키가 올바르지 않아요. GEMINI_API_KEY 를 확인해 주세요.") from e
                if e.code == 429:
                    last_error = VisionError("AI 무료 사용량을 잠시 다 썼어요. 1분쯤 뒤에 다시 시도해 주세요.")
                    break  # 모델마다 한도가 따로라 예비 모델로
                if e.code == 404:
                    last_error = VisionError(f"AI 모델 '{model}' 을 찾을 수 없어요. GEMINI_MODEL 을 확인해 주세요.")
                    break
                raise VisionError("AI 분석 요청이 거절됐어요. 다른 사진으로 시도해 주세요.") from e
            except genai_errors.APIError as e:  # 5xx: 서버 혼잡·일시 오류
                log.warning("Gemini 서버 오류 (%s, %d번째 시도): %s", model, attempt + 1, e)
                last_error = busy
                if attempt < len(RETRY_DELAYS):
                    time.sleep(RETRY_DELAYS[attempt])
                continue
            except httpx.TimeoutException:
                log.warning("Gemini 응답 시간 초과 (%s, %d번째 시도, %ds)", model, attempt + 1, REQUEST_TIMEOUT_S)
                last_error = busy
                break  # 같은 모델은 또 오래 걸릴 가능성이 커서 예비 모델로
            except Exception as e:  # 네트워크 끊김, 방화벽 등
                log.exception("Gemini 연결 실패")
                raise VisionError("AI 서버에 연결할 수 없어요. 인터넷 연결을 확인해 주세요.") from e

            try:
                analysis = ClothingAnalysis.model_validate_json(response.text or "")
            except (ValidationError, ValueError) as e:
                log.warning("Gemini 응답 형식 오류 (%s): %r", model, getattr(response, "text", None))
                raise VisionError("AI 응답을 이해하지 못했어요. 다시 시도해 주세요.") from e
            if model != settings.gemini_model:
                log.info("예비 모델 %s 로 분석함", model)
            return analysis, {"model": model, "result": analysis.model_dump(mode="json")}

    raise last_error or VisionError("AI 분석에 실패했어요. 잠시 후 다시 시도해 주세요.")
