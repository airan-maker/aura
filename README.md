# Aura: 차세대 SEO & AEO 통합 분석 플랫폼

Aura는 전통적인 SEO(Search Engine Optimization)와 AI Engine Optimization(AEO)을 통합하여 기업이 Google 검색 및 AI 답변 엔진(ChatGPT, Gemini 등)에서 최우선 추천되도록 돕는 분석 플랫폼입니다.

## 주요 기능

### SEO 분석 (6개 카테고리)
- **메타태그 분석**: Title, Description, OG Tags 검증
- **헤딩 구조**: H1-H6 계층 구조 및 최적화 확인
- **성능 분석**: 페이지 로딩 속도 측정
- **모바일 최적화**: 반응형 디자인 검증
- **보안**: HTTPS 사용 여부 확인
- **구조화된 데이터**: JSON-LD Schema.org 데이터 감지

### AEO 분석 (AI 기반)
- **브랜드 명확성**: OpenAI GPT-4가 평가한 브랜드 이해도
- **가치 제안**: 제품/서비스 명확성 분석
- **대상 고객**: 타겟 오디언스 식별
- **고유 가치**: 차별화 요소 분석

### 실시간 대시보드
- URL 입력 즉시 분석 시작
- WebSocket 기반 실시간 진행 상황 표시
- 종합 점수 및 상세 메트릭 시각화
- 우선순위별 개선 권장사항 제공

## 기술 스택

### Backend
- **FastAPI**: 비동기 Python 웹 프레임워크
- **PostgreSQL**: 관계형 데이터베이스
- **Playwright**: JavaScript 렌더링 크롤러
- **OpenAI GPT-4**: AI 분석 엔진
- **SQLAlchemy + Alembic**: ORM 및 마이그레이션

### Frontend
- **Next.js 14**: React 기반 풀스택 프레임워크
- **TypeScript**: 타입 안전성
- **Tailwind CSS**: 유틸리티 기반 스타일링
- **WebSocket**: 실시간 업데이트

## 빠른 시작

### 필수 요구사항
- Docker & Docker Compose
- OpenAI API Key

### 설치 및 실행

1. **환경 변수 설정**
```bash
# 루트 디렉토리에 .env 파일 생성
echo "OPENAI_API_KEY=sk-your-key-here" > .env
echo "SECRET_KEY=your-secret-key-change-in-production" >> .env
```

2. **전체 스택 실행**
```bash
docker-compose up -d
```

3. **데이터베이스 마이그레이션**
```bash
docker-compose exec backend alembic upgrade head
```

4. **애플리케이션 접속**
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000/docs

### 첫 분석 실행

1. 브라우저에서 http://localhost:3000 접속
2. URL 입력 (예: https://example.com)
3. "Analyze Website" 버튼 클릭
4. 실시간 진행 상황 확인 (60-90초 소요)
5. 완료 후 자동으로 리포트 페이지로 이동
6. SEO/AEO 점수 및 개선 권장사항 확인

## 문서

- **[설치 및 실행 가이드](SETUP_GUIDE.md)** - 상세 설치 및 설정 방법
- **[테스트 가이드](TEST_GUIDE.md)** - 수동 테스트 시나리오
- **[테스트 문서](TESTING.md)** - 자동화 테스트 실행 방법
- **[프론트엔드 README](frontend/README.md)** - 프론트엔드 상세 문서

## 프로젝트 구조

```
aura/
├── backend/                 # FastAPI 백엔드
│   ├── app/
│   │   ├── api/v1/         # REST API 엔드포인트
│   │   ├── models/         # 데이터베이스 모델
│   │   ├── services/       # 비즈니스 로직
│   │   ├── workers/        # 백그라운드 작업
│   │   └── core/           # 공통 유틸리티
│   ├── tests/              # pytest 테스트
│   └── alembic/            # DB 마이그레이션
│
├── frontend/               # Next.js 프론트엔드
│   ├── src/
│   │   ├── app/           # Next.js 페이지
│   │   ├── components/    # React 컴포넌트
│   │   ├── lib/           # API 클라이언트
│   │   └── hooks/         # React Hooks
│   └── e2e/               # Playwright E2E 테스트
│
├── scripts/               # 테스트 및 유틸리티 스크립트
└── docker-compose.yml     # 컨테이너 설정
```

## 테스트

### 빠른 헬스 체크
```bash
./scripts/quick-test.sh
```

### 전체 시스템 테스트
```bash
./scripts/test-system.sh
```

### 백엔드 테스트
```bash
cd backend
pytest -v
```

### 프론트엔드 E2E 테스트
```bash
cd frontend
npm install
npx playwright install
npm test
```

상세한 테스트 방법은 [TESTING.md](TESTING.md) 참조

## 개발 로드맵

### Phase 1 (완료 ✅)
- [x] 웹 크롤링 (Playwright)
- [x] SEO 분석 (6개 카테고리)
- [x] LLM 분석 (OpenAI GPT-4)
- [x] REST API + WebSocket
- [x] Next.js 프론트엔드
- [x] 실시간 진행 추적
- [x] 리포트 대시보드
- [x] E2E 테스트

### Phase 2 (계획)
- [ ] 경쟁사 비교 분석
- [ ] Schema.org 자동 생성기
- [ ] PDF 리포트 다운로드
- [ ] 사용자 인증 시스템

### Phase 3 (계획)
- [ ] AI 엔진별 SOV 대시보드
- [ ] 다중 LLM 지원 (Claude, Gemini)
- [ ] 주기적 재분석 스케줄링

## 라이선스

MIT License

---

**Aura** - AI 시대를 위한 SEO 플랫폼
