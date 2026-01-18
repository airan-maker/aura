# Aura 테스트 가이드

## Phase 1.7: 테스트 및 안정화

이 가이드는 Aura 시스템을 테스트하고 안정화하는 방법을 설명합니다.

## 사전 준비

### 1. 시스템 실행 확인

```bash
# 전체 스택 실행
docker-compose up -d

# 모든 서비스 상태 확인
docker-compose ps

# 로그 확인
docker-compose logs -f
```

예상 출력:
```
NAME                COMMAND                  SERVICE    STATUS
aura-backend        "uvicorn app.main:ap…"   backend    Up
aura-frontend       "npm run dev"            frontend   Up
aura-postgres       "docker-entrypoint.s…"   db         Up (healthy)
```

### 2. 데이터베이스 마이그레이션 확인

```bash
docker-compose exec backend alembic current
```

출력이 `20250117_0000 (head)`를 표시해야 합니다.

### 3. 서비스 접근 확인

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000/docs
- Health Check: http://localhost:8000/api/v1/health

## 테스트 시나리오

### 시나리오 1: 잘 최적화된 사이트 (높은 점수 예상)

**테스트 URL**: `https://example.com`

**예상 결과:**
- SEO 점수: 70-85
- AEO 점수: 60-75
- 분석 시간: 60-90초

**테스트 단계:**
1. Frontend (http://localhost:3000)에 접속
2. URL 입력: `https://example.com`
3. "Analyze Website" 버튼 클릭
4. 진행 상황 모니터링 (0% → 30% → 60% → 90% → 100%)
5. 자동으로 리포트 페이지로 이동 확인
6. 점수 및 메트릭 확인

**확인 항목:**
- ✓ URL 검증 통과
- ✓ 분석 요청 생성 (status: pending)
- ✓ WebSocket 연결 성공 (실시간 업데이트)
- ✓ 크롤링 완료 (progress: 30%)
- ✓ SEO 분석 완료 (progress: 60%)
- ✓ LLM 분석 완료 (progress: 90%)
- ✓ 결과 저장 (progress: 100%, status: completed)
- ✓ 리포트 표시 (SEO/AEO 점수, 메트릭, 추천사항)

### 시나리오 2: 최적화되지 않은 사이트 (낮은 점수 예상)

**테스트 URL**: `http://info.cern.ch` (최초 웹사이트 - 기본적인 HTML)

**예상 결과:**
- SEO 점수: 30-50 (메타태그 부족, 느린 성능, HTTP only)
- AEO 점수: 40-60
- 분석 시간: 60-90초

**테스트 단계:**
1. 새 분석 시작
2. URL 입력: `http://info.cern.ch`
3. 분석 완료 대기
4. 낮은 점수 및 많은 추천사항 확인

**확인 항목:**
- ✓ HTTP 사이트 처리 (HTTPS 없음 경고)
- ✓ 낮은 SEO 점수 표시
- ✓ 많은 이슈 및 추천사항 생성
- ✓ 우선순위별 필터링 작동

### 시나리오 3: 현대적인 SPA (JavaScript 렌더링)

**테스트 URL**: `https://react.dev`

**예상 결과:**
- SEO 점수: 75-90
- AEO 점수: 80-95
- 분석 시간: 60-90초

**확인 항목:**
- ✓ JavaScript 렌더링 콘텐츠 추출
- ✓ 메타태그 정확히 추출
- ✓ 구조화된 데이터 감지
- ✓ 모바일 최적화 확인

### 시나리오 4: 에러 처리 테스트

#### 4.1 잘못된 URL

**테스트 입력**: `not-a-valid-url`

**예상 결과:**
- 에러 메시지: "Please enter a valid HTTP or HTTPS URL"
- 제출 차단

#### 4.2 존재하지 않는 도메인

**테스트 입력**: `https://this-domain-definitely-does-not-exist-12345.com`

**예상 결과:**
- 분석 시작
- 크롤링 단계에서 실패
- status: failed
- 에러 메시지 표시

#### 4.3 접근 불가능한 내부 IP (SSRF 방어)

**테스트 입력**: `http://localhost:8000`

**예상 결과:**
- 에러 메시지: "Invalid URL format or potentially unsafe URL"
- 제출 차단

### 시나리오 5: 동시 분석

**테스트:**
1. 첫 번째 탭에서 `https://example.com` 분석 시작
2. 두 번째 탭에서 `https://react.dev` 분석 시작
3. 세 번째 탭에서 `https://github.com` 분석 시작

**확인 항목:**
- ✓ 모든 분석이 독립적으로 진행
- ✓ 각 분석의 WebSocket 연결 독립적으로 작동
- ✓ 동시 실행 제한 적용 (MAX_CONCURRENT_ANALYSES=5)

### 시나리오 6: 네트워크 복원력

#### 6.1 WebSocket 연결 끊김

**테스트:**
1. 분석 시작
2. 개발자 도구 → Network → Offline 설정
3. 5초 대기
4. Online으로 복원

**예상 결과:**
- WebSocket 끊김 감지
- 폴링으로 자동 전환
- 진행 상황 계속 업데이트

#### 6.2 Backend 재시작

**테스트:**
```bash
docker-compose restart backend
```

**예상 결과:**
- 진행 중인 분석은 실패 처리
- 새 분석 정상 작동

## 수동 테스트 체크리스트

### Frontend UI

- [ ] 홈페이지 로딩
- [ ] URL 입력 폼 렌더링
- [ ] URL 검증 (유효한 URL)
- [ ] URL 검증 (잘못된 URL)
- [ ] "Analyze Website" 버튼 클릭
- [ ] 로딩 상태 표시
- [ ] 분석 진행 페이지로 이동
- [ ] 진행률 바 애니메이션
- [ ] 현재 단계 텍스트 업데이트
- [ ] 완료 후 리포트 페이지로 자동 이동
- [ ] SEO 점수 게이지 렌더링
- [ ] AEO 점수 게이지 렌더링
- [ ] 점수 색상 (녹색: 80+, 노란색: 60-79, 빨간색: <60)
- [ ] SEO 메트릭 카드 표시
- [ ] AEO 인사이트 카드 표시
- [ ] 추천사항 목록 표시
- [ ] 추천사항 필터 (All, High, Medium, Low)
- [ ] "New Analysis" 버튼으로 홈으로 복귀

### Backend API

```bash
# Health check
curl http://localhost:8000/api/v1/health

# 분석 생성
curl -X POST http://localhost:8000/api/v1/analysis \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'

# 응답에서 ID 복사 (예: 550e8400-e29b-41d4-a716-446655440000)

# 상태 확인
curl http://localhost:8000/api/v1/analysis/550e8400-e29b-41d4-a716-446655440000

# 결과 확인 (완료 후)
curl http://localhost:8000/api/v1/analysis/550e8400-e29b-41d4-a716-446655440000/results

# 분석 목록
curl http://localhost:8000/api/v1/analysis
```

### WebSocket

브라우저 콘솔에서:
```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/analysis/YOUR_REQUEST_ID/ws');
ws.onmessage = (e) => console.log('Received:', JSON.parse(e.data));
ws.onopen = () => console.log('Connected');
ws.onerror = (e) => console.error('Error:', e);
ws.onclose = () => console.log('Disconnected');
```

## 성능 테스트

### 분석 시간 측정

```bash
# 시작 시간 기록
time curl -X POST http://localhost:8000/api/v1/analysis \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}' \
  -s | jq -r '.id' | xargs -I {} sh -c 'while true; do STATUS=$(curl -s http://localhost:8000/api/v1/analysis/{} | jq -r ".status"); echo "Status: $STATUS"; [ "$STATUS" = "completed" ] && break || [ "$STATUS" = "failed" ] && break; sleep 2; done'
```

**예상 시간:**
- 총 분석 시간: 60-90초
- 크롤링: ~15초
- SEO 분석: ~5초
- LLM 분석: ~30-40초
- 저장: ~1초

### 리소스 사용량

```bash
# Docker 컨테이너 리소스 확인
docker stats

# 예상 사용량:
# Backend: CPU 10-30%, MEM 200-400MB
# Frontend: CPU 5-10%, MEM 100-200MB
# PostgreSQL: CPU 5-10%, MEM 50-100MB
```

## E2E 테스트 (자동화)

### Backend 테스트

기존 pytest 테스트 실행:
```bash
cd backend
pytest -v

# 커버리지 포함
pytest --cov=app --cov-report=html

# 특정 테스트만 실행
pytest tests/test_services/test_crawler.py -v
pytest tests/test_services/test_seo_analyzer.py -v
pytest tests/test_services/test_llm_analyzer.py -v
```

### Frontend E2E 테스트 (Playwright)

프론트엔드 E2E 테스트를 추가할 예정입니다.

## 알려진 제한사항

1. **OpenAI API Rate Limit**
   - 분당 요청 제한 있음
   - 실패 시 자동 재시도 (최대 3회)

2. **크롤링 타임아웃**
   - 기본값: 30초
   - 매우 느린 사이트는 실패 가능

3. **동시 분석 제한**
   - 최대 5개 동시 분석 (MAX_CONCURRENT_ANALYSES)
   - 초과 시 대기

4. **스크린샷 저장**
   - 로컬 파일 시스템에 저장
   - 프로덕션에서는 S3 등 사용 권장

## 버그 리포트 템플릿

버그 발견 시:

```markdown
### 버그 설명
[간단한 설명]

### 재현 단계
1. ...
2. ...
3. ...

### 예상 동작
[무엇이 일어나야 하는가]

### 실제 동작
[무엇이 일어났는가]

### 환경
- OS: [Windows/Mac/Linux]
- Browser: [Chrome/Firefox/Safari]
- Backend 로그: [docker-compose logs backend]
- Frontend 콘솔 에러: [브라우저 콘솔 출력]

### 스크린샷
[가능하다면]
```

## 다음 단계

테스트 완료 후:
1. 발견된 버그 수정
2. 성능 병목 지점 개선
3. 에러 메시지 개선
4. 사용자 경험 향상
5. Phase 1.8 배포 준비

## 성공 기준

Phase 1.7 완료 조건:
- [ ] 10개 이상의 다양한 웹사이트 테스트 완료
- [ ] 분석 성공률 90% 이상
- [ ] 평균 분석 시간 90초 이내
- [ ] 모든 UI 컴포넌트 정상 작동
- [ ] 에러 처리 적절함
- [ ] Backend 단위 테스트 100% 통과
- [ ] E2E 테스트 작성 및 통과
- [ ] 문서화 완료
