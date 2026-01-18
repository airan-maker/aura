# Aura 설치 및 실행 가이드

## Phase 1 MVP 완료! ✅

현재 구현된 기능:
- ✅ 웹 크롤링 (Playwright)
- ✅ SEO 분석 (메타태그, 헤딩, 성능, 모바일, HTTPS, Structured Data)
- ✅ LLM 분석 (OpenAI GPT-4 브랜드 인지도)
- ✅ 백그라운드 작업 처리
- ✅ REST API 엔드포인트
- ✅ WebSocket 실시간 진행 상황
- ✅ PostgreSQL 데이터베이스
- ✅ Next.js 프론트엔드
- ✅ 반응형 UI 대시보드
- ✅ 실시간 진행 추적
- ✅ 점수 시각화 및 리포트

## 빠른 시작

### 1. 환경 변수 설정

루트 디렉토리에 `.env` 파일 생성:

```bash
# .env
OPENAI_API_KEY=sk-your-openai-api-key-here
SECRET_KEY=your-secret-key-here
```

Backend 디렉토리에도 `.env` 파일 생성:

```bash
cd backend
cp .env.example .env
```

`.env` 파일 편집:
```bash
DATABASE_URL=postgresql+asyncpg://aura:aura_password@localhost:5432/aura
OPENAI_API_KEY=sk-your-openai-api-key-here
SECRET_KEY=your-secret-key-change-in-production
ALLOWED_ORIGINS=["http://localhost:3000"]
CRAWLER_TIMEOUT=30000
MAX_CONCURRENT_ANALYSES=5
ENVIRONMENT=development
```

### 2. Docker Compose로 전체 스택 실행

```bash
# 전체 스택 시작 (PostgreSQL + Backend + Frontend)
docker-compose up -d

# 로그 확인
docker-compose logs -f

# 또는 개별 서비스 로그 확인
docker-compose logs -f backend
docker-compose logs -f frontend
```

### 3. 데이터베이스 마이그레이션

```bash
# Backend 컨테이너 내부에서 실행
docker-compose exec backend alembic upgrade head
```

### 4. 애플리케이션 접속

브라우저에서 다음 URL 열기:
- **Frontend**: http://localhost:3000 (메인 애플리케이션)
- **Backend API Docs**: http://localhost:8000/docs (Swagger UI)
- **Backend ReDoc**: http://localhost:8000/redoc

## 로컬 개발 환경 (Docker 없이)

### Backend 설정

```bash
cd backend

# Python 가상환경 생성
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

# 의존성 설치
pip install -r requirements.txt

# Playwright 브라우저 설치
playwright install chromium

# 환경 변수 설정
cp .env.example .env
# .env 파일 편집 (위 참조)

# PostgreSQL 시작 (별도 터미널)
docker-compose up db

# 데이터베이스 마이그레이션
alembic upgrade head

# 개발 서버 실행
uvicorn app.main:app --reload
```

**Backend 접속:**
- API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Frontend 설정

```bash
cd frontend

# 의존성 설치
npm install

# 환경 변수 설정
echo "NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1" > .env.local

# 개발 서버 실행
npm run dev
```

**Frontend 접속:**
- Application: http://localhost:3000

## 사용 방법

### 웹 UI를 통한 분석

1. 브라우저에서 http://localhost:3000 접속
2. 분석하고 싶은 웹사이트 URL 입력 (예: https://example.com)
3. "Analyze Website" 버튼 클릭
4. 분석 진행 상황 실시간 확인
5. 완료 후 자동으로 리포트 페이지로 이동
6. SEO/AEO 점수 및 상세 분석 결과 확인
7. 우선순위별 개선 권장사항 확인

### 주요 기능

- **SEO 점수**: 메타태그, 성능, 모바일 최적화 등 종합 평가
- **AEO 점수**: AI 엔진이 이해한 브랜드 명확성 평가
- **상세 메트릭**: 각 항목별 세부 분석 결과
- **개선 권장사항**: 우선순위별로 필터링 가능한 추천 목록

## API 사용 예시 (직접 호출)

### 1. 분석 요청 생성

```bash
curl -X POST "http://localhost:8000/api/v1/analysis" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
```

응답:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "url": "https://example.com",
  "status": "pending",
  "progress": 0,
  "created_at": "2025-01-17T00:00:00Z"
}
```

### 2. 분석 상태 확인

```bash
curl "http://localhost:8000/api/v1/analysis/550e8400-e29b-41d4-a716-446655440000"
```

응답:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "url": "https://example.com",
  "status": "processing",
  "progress": 45,
  "current_step": "Analyzing SEO metrics",
  "created_at": "2025-01-17T00:00:00Z",
  "started_at": "2025-01-17T00:00:05Z"
}
```

### 3. 분석 결과 조회

```bash
curl "http://localhost:8000/api/v1/analysis/550e8400-e29b-41d4-a716-446655440000/results"
```

응답:
```json
{
  "id": "...",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "url": "https://example.com",
  "seo_score": 87.5,
  "seo_metrics": {
    "meta_tags": {...},
    "headings": {...},
    "load_time": 1.8,
    ...
  },
  "aeo_score": 82.3,
  "aeo_metrics": {
    "what_it_does": "Example domain for testing",
    "clarity_score": 8,
    ...
  },
  "recommendations": [
    {
      "category": "seo",
      "priority": "high",
      "title": "Add Meta Description",
      "description": "...",
      "impact": "high"
    }
  ],
  "analysis_duration": 45.2,
  "created_at": "2025-01-17T00:01:00Z"
}
```

### 4. WebSocket 실시간 업데이트

JavaScript 예시:
```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/analysis/550e8400-e29b-41d4-a716-446655440000/ws');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(`Progress: ${data.progress}% - ${data.step}`);
};

// Keep alive
setInterval(() => {
  ws.send('ping');
}, 30000);
```

## 테스트 실행

```bash
cd backend

# 전체 테스트 실행
pytest -v

# 특정 모듈 테스트
pytest tests/test_services/test_crawler.py -v
pytest tests/test_services/test_seo_analyzer.py -v
pytest tests/test_services/test_llm_analyzer.py -v

# 커버리지 리포트
pytest --cov=app --cov-report=html

# HTML 리포트 확인
# htmlcov/index.html 열기
```

## 데이터베이스 관리

```bash
# 새 마이그레이션 생성
alembic revision --autogenerate -m "description"

# 마이그레이션 적용
alembic upgrade head

# 마이그레이션 롤백
alembic downgrade -1

# 현재 버전 확인
alembic current

# 마이그레이션 히스토리
alembic history
```

## 문제 해결

### "No module named 'app'" 에러
```bash
# PYTHONPATH 설정
export PYTHONPATH="${PYTHONPATH}:${PWD}"  # Linux/Mac
set PYTHONPATH=%PYTHONPATH%;%CD%  # Windows
```

### Playwright 브라우저 없음
```bash
playwright install chromium
```

### PostgreSQL 연결 실패
```bash
# PostgreSQL 실행 확인
docker-compose ps

# PostgreSQL 로그 확인
docker-compose logs db

# PostgreSQL 재시작
docker-compose restart db
```

### OpenAI API 키 오류
- `.env` 파일에 올바른 API 키가 설정되어 있는지 확인
- API 키가 `sk-`로 시작하는지 확인
- OpenAI 계정에 크레딧이 있는지 확인

### Frontend 연결 오류
- Backend가 http://localhost:8000에서 실행 중인지 확인
- `.env.local`의 `NEXT_PUBLIC_API_URL` 확인
- CORS 설정이 올바른지 확인 (backend/app/main.py)
- 브라우저 콘솔에서 에러 확인

### WebSocket 연결 실패
- Backend WebSocket 엔드포인트 확인
- 방화벽/프록시 설정 확인
- WebSocket 실패 시 폴링으로 자동 전환됨

## Phase 1 MVP 완료!

Phase 1에서 구현된 모든 기능:
- ✅ Next.js 프론트엔드
- ✅ URL 입력 폼
- ✅ 분석 진행 상황 표시 (실시간)
- ✅ 리포트 대시보드
- ✅ SEO/AEO 점수 시각화
- ✅ 우선순위별 추천사항 목록
- ✅ 반응형 디자인

## 다음 단계 (Phase 2 이후)

향후 구현 가능한 기능:
- [ ] 경쟁사 비교 분석
- [ ] Schema.org 자동 생성기
- [ ] PDF 리포트 다운로드
- [ ] AI 엔진별 SOV 대시보드 (ChatGPT, Gemini, Perplexity)
- [ ] 사용자 인증 시스템
- [ ] 분석 히스토리 및 추이 분석
- [ ] 주기적 재분석 스케줄링
- [ ] 다중 페이지 분석

## 프로젝트 구조

```
aura/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # API 엔드포인트
│   │   │   ├── analysis.py  # 분석 엔드포인트 + WebSocket
│   │   │   └── health.py    # 헬스체크
│   │   ├── models/          # 데이터베이스 모델
│   │   │   └── analysis.py  # AnalysisRequest, AnalysisResult
│   │   ├── schemas/         # Pydantic 스키마
│   │   ├── services/        # 비즈니스 로직
│   │   │   ├── crawler.py   # Playwright 크롤러
│   │   │   ├── seo_analyzer.py  # SEO 분석
│   │   │   ├── llm_analyzer.py  # GPT-4 분석
│   │   │   └── orchestrator.py  # 파이프라인 조율
│   │   ├── workers/         # 백그라운드 작업
│   │   │   └── analysis_worker.py
│   │   ├── core/            # 공통 유틸리티
│   │   │   ├── exceptions.py
│   │   │   └── security.py
│   │   └── utils/
│   │       └── validators.py
│   ├── alembic/             # DB 마이그레이션
│   ├── tests/               # 테스트
│   ├── storage/             # 스크린샷 저장소
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── app/             # Next.js App Router
│   │   │   ├── page.tsx    # 홈 (URL 입력)
│   │   │   ├── analysis/[id]/page.tsx  # 분석 진행
│   │   │   ├── report/[id]/page.tsx    # 리포트 대시보드
│   │   │   ├── layout.tsx  # 루트 레이아웃
│   │   │   └── globals.css
│   │   ├── components/
│   │   │   ├── ui/         # 기본 UI 컴포넌트
│   │   │   ├── analysis/   # 분석 컴포넌트
│   │   │   └── report/     # 리포트 컴포넌트
│   │   ├── lib/
│   │   │   └── api-client.ts
│   │   ├── hooks/
│   │   │   ├── useAnalysis.ts
│   │   │   └── useWebSocket.ts
│   │   └── types/
│   │       └── index.ts
│   ├── package.json
│   └── tsconfig.json
│
└── docker-compose.yml
```

## 지원

문제가 발생하면 다음을 확인하세요:
1. `.env` 파일이 올바르게 설정되었는지
2. PostgreSQL이 실행 중인지
3. 모든 의존성이 설치되었는지 (Python + Node.js)
4. Playwright 브라우저가 설치되었는지

로그 확인:
```bash
# 전체 로그
docker-compose logs -f

# Backend 로그
docker-compose logs -f backend

# Frontend 로그
docker-compose logs -f frontend

# PostgreSQL 로그
docker-compose logs -f db
```

## 개발 워크플로우

1. **새 기능 개발**
   - Backend: `backend/app/services/`에 새 서비스 추가
   - Frontend: `frontend/src/components/`에 새 컴포넌트 추가

2. **데이터베이스 변경**
   - 모델 수정: `backend/app/models/`
   - 마이그레이션 생성: `alembic revision --autogenerate -m "description"`
   - 마이그레이션 적용: `alembic upgrade head`

3. **테스트**
   - Backend: `pytest -v`
   - Frontend: 브라우저 테스트

4. **배포 준비**
   - 환경 변수 프로덕션용으로 변경
   - `SECRET_KEY` 변경 필수
   - `ENVIRONMENT=production` 설정
   - OpenAI API 키 확인
