"""Gemini 호출 공통 모듈 — 사진 분석(기능 1)과 코디 추천(기능 2·3)이 함께 쓴다.

재시도, 예비 모델 전환, 시간 제한, thinking 최소화, 오류 메시지 변환을 여기서 처리한다.
"""

import logging
import time
from typing import TypeVar

import httpx
import httpx2  # google-genai SDK 가 내부에서 쓰는 HTTP 라이브러리
from google import genai
from google.genai import errors as genai_errors
from google.genai import types
from pydantic import BaseModel, ValidationError

from app.core.config import settings

log = logging.getLogger(__name__)

RETRY_DELAYS = (2,)  # 서버 혼잡(5xx) 시 같은 모델로 재시도하기 전 대기 시간(초)
REQUEST_TIMEOUT_S = 25  # 요청 1번의 최대 대기 시간
TOTAL_BUDGET_S = 60  # 재시도·예비 모델 포함 전체 최대 시간


# 응답 시간 초과 예외 (SDK 버전에 따라 httpx / httpx2 중 하나를 씀)
TIMEOUT_ERRORS = (httpx.TimeoutException, httpx2.TimeoutException)


class AIError(Exception):
    """사용자에게 보여 줄 메시지를 담은 AI 호출 실패."""


_client: genai.Client | None = None
_no_thinking_config: set[str] = set()  # thinking_level 을 지원하지 않는 모델 (한 번 거절되면 기억)

T = TypeVar("T", bound=BaseModel)


def _get_client() -> genai.Client:
    global _client
    if not settings.gemini_api_key:
        raise AIError("AI 키가 설정되지 않았어요. backend/.env 의 GEMINI_API_KEY 를 확인해 주세요.")
    if _client is None:
        _client = genai.Client(
            api_key=settings.gemini_api_key,
            http_options=types.HttpOptions(timeout=REQUEST_TIMEOUT_S * 1000),  # 응답이 없으면 끊기
        )
    return _client


def _models() -> list[str]:
    models = [settings.gemini_model]
    if settings.gemini_fallback_model and settings.gemini_fallback_model not in models:
        models.append(settings.gemini_fallback_model)
    return models


def _call(client: genai.Client, model: str, contents: list, schema: type[BaseModel], temperature: float):
    # 옷 분류·코디 고르기는 깊게 '생각'할 필요가 없어서 thinking 을 최소로 줄여 응답을 빠르게 한다
    thinking = None
    if settings.gemini_thinking and model not in _no_thinking_config:
        thinking = types.ThinkingConfig(thinking_level=settings.gemini_thinking.upper())
    return client.models.generate_content(
        model=model,
        contents=contents,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=schema,
            temperature=temperature,
            thinking_config=thinking,
        ),
    )


def generate(contents: list, schema: type[T], temperature: float = 0.2) -> tuple[T, str]:
    """Gemini 에 contents(텍스트·이미지)를 보내 schema 형식의 JSON 을 받는다. (검증된 결과, 사용한 모델)

    서버 혼잡이면 재시도하고, 안 되면 예비 모델(GEMINI_FALLBACK_MODEL)로 바꿔 시도한다.
    """
    client = _get_client()
    last_error: AIError | None = None
    started = time.monotonic()
    busy = AIError("AI 서버가 지금 붐벼요. 잠시 후 다시 시도해 주세요.")

    for model in _models():
        for attempt in range(len(RETRY_DELAYS) + 1):
            if time.monotonic() - started > TOTAL_BUDGET_S:
                log.warning("Gemini 시간 초과 (%ds) — 중단", TOTAL_BUDGET_S)
                raise last_error or busy
            try:
                response = _call(client, model, contents, schema, temperature)
            except genai_errors.ClientError as e:
                if e.code == 400 and "think" in str(e).lower() and model not in _no_thinking_config:
                    log.info("%s 는 thinking 설정을 지원하지 않아 기본값으로 다시 요청", model)
                    _no_thinking_config.add(model)
                    continue
                log.warning("Gemini 요청 오류 (%s): %s", model, e)
                if e.code in (400, 401, 403) and "API key" in str(e):
                    raise AIError("AI 키가 올바르지 않아요. GEMINI_API_KEY 를 확인해 주세요.") from e
                if e.code == 429:
                    last_error = AIError("AI 무료 사용량을 잠시 다 썼어요. 1분쯤 뒤에 다시 시도해 주세요.")
                    break  # 모델마다 한도가 따로라 예비 모델로
                if e.code == 404:
                    last_error = AIError(f"AI 모델 '{model}' 을 찾을 수 없어요. GEMINI_MODEL 을 확인해 주세요.")
                    break
                raise AIError("AI 요청이 거절됐어요. 다른 사진이나 조건으로 다시 시도해 주세요.") from e
            except genai_errors.APIError as e:  # 5xx: 서버 혼잡·일시 오류
                log.warning("Gemini 서버 오류 (%s, %d번째 시도): %s", model, attempt + 1, e)
                last_error = busy
                if attempt < len(RETRY_DELAYS):
                    time.sleep(RETRY_DELAYS[attempt])
                continue
            except TIMEOUT_ERRORS:
                log.warning("Gemini 응답 시간 초과 (%s, %d번째 시도, %ds)", model, attempt + 1, REQUEST_TIMEOUT_S)
                last_error = busy
                break  # 같은 모델은 또 오래 걸릴 가능성이 커서 예비 모델로
            except Exception as e:  # 네트워크 끊김, 방화벽 등
                log.exception("Gemini 연결 실패")
                raise AIError("AI 서버에 연결할 수 없어요. 인터넷 연결을 확인해 주세요.") from e

            try:
                result = schema.model_validate_json(response.text or "")
            except (ValidationError, ValueError) as e:
                log.warning("Gemini 응답 형식 오류 (%s): %r", model, getattr(response, "text", None))
                raise AIError("AI 응답을 이해하지 못했어요. 다시 시도해 주세요.") from e
            if model != settings.gemini_model:
                log.info("예비 모델 %s 로 분석함", model)
            return result, model

    raise last_error or AIError("AI 분석에 실패했어요. 잠시 후 다시 시도해 주세요.")
