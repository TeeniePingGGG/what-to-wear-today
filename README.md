# 🥻 오늘 뭐 입지?

> 내 옷장 사진과 실시간 날씨·일정 데이터로 매일 아침 코디를 추천하는 AI 스타일리스트 반응형 웹앱

## 기술 스택

| 영역 | 기술 |
|---|---|
| Frontend | React 19 · TypeScript · Vite · React Router · TanStack Query · axios · CSS Modules |
| Backend | Python 3.12+ · FastAPI · SQLAlchemy 2 · Alembic · JWT 인증 |
| Database | MySQL 8.0 |
| AI · 외부 API | Gemini (옷 사진 분석, 코디 추천) · rembg (배경 제거) · Open-Meteo (날씨, 키 없음) |

## 폴더 구조

```
what-to-wear-today/
├─ backend/                 FastAPI 서버
│  ├─ app/
│  │  ├─ api/routes/        API 라우터 (auth, clothes)
│  │  ├─ core/              설정(.env), 보안(JWT·비밀번호)
│  │  ├─ db/                DB 연결, Base 모델
│  │  ├─ models/            테이블 정의 (SQLAlchemy)
│  │  ├─ schemas/           요청/응답 형식 (Pydantic)
│  │  └─ main.py
│  ├─ alembic/              DB 마이그레이션
│  ├─ requirements.txt
│  └─ .env.example
├─ frontend/                React 앱
│  └─ src/
│     ├─ api/               API 호출 + React Query 훅
│     ├─ auth/              토큰 저장, 로그인 가드
│     ├─ components/        레이아웃(하단 탭바 ↔ 사이드바), 아이콘
│     ├─ pages/             화면 (오늘, 일정 입력, 가이드, 옷장, 옷 등록, 로그인 …)
│     ├─ mocks/             AI 기능 연동 전 샘플 데이터
│     ├─ styles/            디자인 토큰, 공통 스타일
│     └─ types/             백엔드와 맞춘 타입
├─ docs/
│  ├─ database.md           ERD · 테이블 설명 · 설계 포인트
│  └─ schema.sql            MySQL DDL (참고용)
├─ docker-compose.yml       로컬 MySQL
└─ .vscode/                 VS Code 추천 확장 · 디버그 · 태스크 설정
```

## 처음 실행하기

### 0. 준비물
- [VS Code](https://code.visualstudio.com/) — 폴더를 열면 오른쪽 아래에 **추천 확장 설치** 알림이 떠요. 설치하세요.
- [Python 3.12+](https://www.python.org/downloads/) (Windows 설치 시 *Add python.exe to PATH* 체크)
- [Node.js 22 LTS](https://nodejs.org/)
- MySQL 8.0 — 둘 중 하나
  - **A. Docker Desktop** (추천): 아래 1번 명령 하나면 끝
  - **B. MySQL 직접 설치**: [MySQL Installer](https://dev.mysql.com/downloads/installer/) 설치 후 아래 SQL 실행
    ```sql
    CREATE DATABASE wear CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
    CREATE USER 'wear'@'localhost' IDENTIFIED BY 'wear1234';
    GRANT ALL PRIVILEGES ON wear.* TO 'wear'@'localhost';
    ```

### 1. DB 켜기 (Docker 사용 시)
```bash
docker compose up -d
```

### 2. 백엔드
```bash
cd backend
python -m venv .venv
# Windows (PowerShell)
.venv\Scripts\Activate.ps1
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
pip install -r requirements-bg.txt   # 배경 제거 (용량 큼, 선택)
copy .env.example .env      # macOS/Linux: cp .env.example .env
                            # .env 에 GEMINI_API_KEY 입력
alembic upgrade head        # 테이블 생성
uvicorn app.main:app --reload --port 8000
```
- API 문서(Swagger): http://localhost:8000/docs
- 상태 확인: http://localhost:8000/api/health → `{"status":"ok","db":"ok"}`
- VS Code에서 `Ctrl+Shift+P` → **Python: Select Interpreter** → `backend/.venv` 선택

> PowerShell에서 Activate.ps1 실행이 막히면: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

### 3. 프론트엔드 (새 터미널)
```bash
cd frontend
npm install
npm run dev
```
http://localhost:5173 접속 → 회원가입 → 옷 등록. `/api` 요청은 Vite가 8000번으로 넘겨줘요.

### VS Code 단축 실행
- `F5` → **Full Stack (백엔드 + 프론트)**: 서버 두 개를 디버그 모드로 한 번에 실행
- `Ctrl+Shift+P` → **Tasks: Run Task** → `db: up (docker)` / `db: migrate`

## DB 변경하는 법
1. `backend/app/models/` 에서 모델 수정
2. `alembic revision --autogenerate -m "변경 내용"` → `alembic/versions/` 에 생성된 파일 확인
3. `alembic upgrade head`

자세한 테이블 설계는 [docs/database.md](docs/database.md)에 있어요.

## 현재 구현 상태

| 구분 | 상태 |
|---|---|
| 회원가입 / 로그인 / 내 정보 (`/api/auth/*`) | ✅ |
| 옷 등록 · 목록 · 수정 · 삭제 (`/api/clothes`) | ✅ |
| 반응형 레이아웃 (모바일 하단 탭 / 데스크톱 사이드바) | ✅ |
| 홈 · 일정 입력 · 스타일리스트 가이드 화면 | ✅ |
| 기능 1: 배경 제거 + Vision AI 자동 태깅 → 사용자 검수, 여러 벌 한 번에 등록 (`/api/clothes/analyze`, `/api/clothes/bulk`) | ✅ |
| 기능 2: 날씨 API + 일정 + LLM 코디 추천 (`/api/weather`, `/api/schedules`, `/api/recommendations`) | ✅ |
| 기능 3: AI 스타일리스트 가이드 + 피드백 저장·다음 추천 반영 (`/api/outfits/{id}/guide`, `/api/outfits/{id}/feedback`) | ✅ |

