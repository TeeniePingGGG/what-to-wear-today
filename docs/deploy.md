# 무료 배포 가이드 — Vercel + TiDB Cloud

```
[브라우저] ──https──▶ Vercel 프로젝트 ① frontend (React, 정적 파일)
                         │  /api/* 요청은 ②로 넘김 (frontend/vercel.json 의 rewrites)
                         ▼
                      Vercel 프로젝트 ② backend (FastAPI)
                         ├─▶ TiDB Cloud Starter (MySQL 호환 DB, 무료)
                         ├─▶ Vercel Blob (옷 사진, 무료 1GB)
                         └─▶ Gemini · Open-Meteo · OpenStreetMap
```

> 배포 버전에서는 **배경 제거가 꺼져요** (모델이 커서 Vercel 무료 서버에서 못 돌림). 옷은 잘라낸 사진 그대로 저장되고 AI 분석은 그대로 동작해요. 내 컴퓨터에서 실행할 땐 지금처럼 배경 제거가 돼요.

## 0. 준비

- 최신 코드가 GitHub 에 push 돼 있어야 해요 (`git add .` → `git commit` → `git push`).
- 계정: [Vercel](https://vercel.com) (GitHub 로그인, Hobby 플랜), [TiDB Cloud](https://tidbcloud.com) (GitHub 로그인)
- Gemini API 키 (내 컴퓨터 `backend/.env` 에 넣은 것과 같은 키)

---

## 1. DB 만들기 — TiDB Cloud Starter

1. TiDB Cloud 에 로그인 → **Create Cluster** → **Starter** (무료) 선택
2. 지역(Region)은 한국과 가까운 **Tokyo (ap-northeast-1)** 추천 → Create
3. 클러스터 화면 → **Connect** 버튼
   - **Generate Password** 로 비밀번호 생성 → 메모해 두기 (다시 볼 수 없어요)
   - 표시되는 **HOST** (예: `gateway01.ap-northeast-1.prod.aws.tidbcloud.com`), **PORT** (`4000`), **USERNAME** (예: `2abc...root`) 메모
4. 클러스터 화면 → **SQL Editor** 에서 실행:
   ```sql
   CREATE DATABASE wear;
   ```
5. 연결 주소 만들기 (메모장에):
   ```
   mysql+pymysql://USERNAME:PASSWORD@HOST:4000/wear?charset=utf8mb4
   ```
   비밀번호에 `@ : / ? #` 같은 특수문자가 있으면 연결이 깨져요. 그럴 땐 비밀번호를 다시 생성하세요.

## 2. 테이블 만들기 — 내 컴퓨터에서 한 번

VS Code **새 터미널(cmd)** 에서 (이 터미널에서만 TiDB 를 바라보게 임시로 설정):

```
cd backend
.venv\Scripts\activate
pip install -r requirements.txt
set DATABASE_URL=mysql+pymysql://USERNAME:PASSWORD@HOST:4000/wear?charset=utf8mb4
set DB_SSL=true
alembic upgrade head
```

`Running upgrade ... init schema` 와 `... add outfit intro` 두 줄이 나오면 성공. **끝나면 이 터미널은 닫으세요** (닫아야 다시 내 컴퓨터 DB 를 써요).

> PowerShell 이면 `set` 대신 `$env:DATABASE_URL="..."`, `$env:DB_SSL="true"`

## 3. 백엔드 배포 — Vercel 프로젝트 ②

1. Vercel → **Add New… → Project** → GitHub 저장소 `what-to-wear-today` **Import**
2. **Project Name**: `wear-api` 처럼 알아보기 쉽게
3. **Root Directory** → **Edit** → `backend` 선택 (중요!)
4. Framework Preset 이 **FastAPI** 로 잡히는지 확인
5. **Environment Variables** 에 하나씩 추가:

   | Key | Value |
   |---|---|
   | `DATABASE_URL` | 1-5 에서 만든 주소 |
   | `DB_SSL` | `true` |
   | `JWT_SECRET` | 긴 랜덤 문자열 (`python -c "import secrets;print(secrets.token_urlsafe(48))"` 결과) |
   | `GEMINI_API_KEY` | Gemini 키 |
   | `GEMINI_MODEL` | `gemini-3.8-flash` (내 컴퓨터 `.env` 와 같게) |
   | `GEMINI_FALLBACK_MODEL` | `gemini-3.5-flash-lite` |
   | `GEMINI_THINKING` | `minimal` |
   | `STORAGE` | `blob` |
   | `BG_REMOVAL` | `false` |

6. **Deploy** → 1~2분 기다리기
7. 배포가 끝나면 프로젝트 화면 → **Storage** 탭 → **Create → Blob**
   - 이름: `wear-photos`, 접근 방식 **Public** 선택 → 이 프로젝트에 **Connect**
   - 자동으로 `BLOB_READ_WRITE_TOKEN` 환경변수가 추가돼요
8. **Deployments** 탭 → 맨 위 배포의 `⋯` → **Redeploy** (Blob 토큰을 반영하려고)
9. 확인: 브라우저에서 `https://wear-api.vercel.app/api/health` (프로젝트 주소로)
   → `{"status":"ok","db":"ok"}` 이면 성공. `/docs` 로 가면 Swagger 도 보여요.

## 4. 프런트 배포 — Vercel 프로젝트 ①

1. 내 컴퓨터에서 `frontend/vercel.json` 을 열어 `YOUR-BACKEND.vercel.app` 을 **3-9 의 백엔드 주소**로 바꾸기
   ```json
   "destination": "https://wear-api.vercel.app/api/:path*"
   ```
2. GitHub 에 올리기: `git add .` → `git commit -m "배포: 백엔드 주소 설정"` → `git push`
3. Vercel → **Add New… → Project** → 같은 저장소 다시 **Import**
4. **Project Name**: `wear` 처럼 / **Root Directory**: `frontend` / Framework: **Vite** 확인
5. 환경변수는 필요 없어요 → **Deploy**
6. 나온 주소(`https://wear.vercel.app` 등)로 접속 → 회원가입 → 옷 등록 → 코디 추천 해 보기

HTTPS 주소라 휴대폰에서도 위치 권한이 동작해요.

---

## 이후 업데이트

- 코드를 고치고 `git push` 하면 **두 프로젝트 모두 자동으로 다시 배포**돼요.
- DB 테이블이 바뀌는 업데이트(새 마이그레이션)가 있으면 **2번 단계를 다시** 실행하세요.

## 문제가 생기면

| 증상 | 확인할 것 |
|---|---|
| 백엔드 배포 자체가 실패 | 배포 화면의 Build Logs 빨간 줄. Root Directory 가 `backend` 인지 |
| `regions` 관련 오류 | `backend/vercel.json` 에서 `"regions": ["icn1"],` 줄을 지우고 push |
| `/api/health` 가 500 | 프로젝트 → **Logs**. `DATABASE_URL`, `DB_SSL=true` 확인 |
| 사진 올리면 오류 | Blob 을 만들고 **Connect + Redeploy** 했는지, Blob 이 **Public** 인지 |
| 프런트에서 로그인이 안 됨 (404) | `frontend/vercel.json` 의 백엔드 주소가 맞는지 |
| AI 분석·추천 실패 | 백엔드 환경변수 `GEMINI_API_KEY` |

> TiDB 는 MySQL 호환 DB 지만 100% 같지는 않아요. 개발은 MySQL 로 했으니, TiDB 에서만 나는 오류가 있으면 로그를 보고 맞춰 고쳐야 해요.

## 무료 한도 (2026년 기준, 바뀔 수 있음)

- Vercel Hobby: 개인·비상업용. Blob 저장 1GB/월
- TiDB Cloud Starter: 저장 25GiB, 월 2.5억 Request Unit
- Gemini 무료 등급: 분당·일일 요청 한도 있음 (AI Studio 에서 확인)
