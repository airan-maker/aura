# Aura 배포 가이드

이 문서는 Aura 플랫폼을 프로덕션 환경에 배포하는 방법을 설명합니다.

## 목차

1. [사전 요구사항](#사전-요구사항)
2. [환경 변수 설정](#환경-변수-설정)
3. [프로덕션 배포](#프로덕션-배포)
4. [SSL/TLS 설정](#ssltls-설정)
5. [데이터베이스 관리](#데이터베이스-관리)
6. [모니터링 및 로깅](#모니터링-및-로깅)
7. [롤백 절차](#롤백-절차)
8. [문제 해결](#문제-해결)

## 사전 요구사항

### 시스템 요구사항

- **OS**: Linux (Ubuntu 20.04+ 권장) 또는 Docker 지원 OS
- **Docker**: 20.10 이상
- **Docker Compose**: 2.0 이상
- **메모리**: 최소 4GB RAM (8GB 권장)
- **디스크**: 최소 20GB 여유 공간
- **포트**: 80, 443, 8000, 3000, 5432 (방화벽 설정 필요)

### 필수 도구 설치

```bash
# Docker 설치 (Ubuntu)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Docker Compose 설치
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 설치 확인
docker --version
docker-compose --version
```

## 환경 변수 설정

### 1. 환경 변수 파일 생성

프로젝트 루트에 `.env` 파일을 생성합니다:

```bash
cp .env.example .env
```

### 2. 필수 환경 변수 설정

`.env` 파일을 편집하여 다음 값들을 설정합니다:

```bash
# OpenAI API (필수)
OPENAI_API_KEY=sk-your-actual-openai-api-key-here

# 보안 키 (필수 - 반드시 변경!)
SECRET_KEY=your-very-long-random-secret-key-here

# 데이터베이스 (필수)
POSTGRES_USER=aura
POSTGRES_PASSWORD=change-this-strong-password
POSTGRES_DB=aura

# 환경 설정
ENVIRONMENT=production

# 데이터베이스 URL
DATABASE_URL=postgresql+asyncpg://aura:change-this-strong-password@db:5432/aura

# CORS 설정 (프로덕션 도메인으로 변경)
ALLOWED_ORIGINS=["https://yourdomain.com","https://www.yourdomain.com"]

# 크롤러 설정
CRAWLER_TIMEOUT=30000
MAX_CONCURRENT_ANALYSES=5

# 로깅
LOG_LEVEL=INFO
```

### 3. SECRET_KEY 생성

강력한 시크릿 키를 생성합니다:

```bash
# Python으로 생성
python -c "import secrets; print(secrets.token_urlsafe(64))"

# OpenSSL로 생성
openssl rand -base64 64 | tr -d '\n'
```

### 4. 환경 변수 검증

```bash
# .env 파일 구문 검사
grep -v '^#' .env | grep -v '^$' | while IFS='=' read -r key value; do
  if [ -z "$value" ] || [ "$value" = "change-this" ] || [ "$value" = "your-" ]; then
    echo "Warning: $key may not be properly configured"
  fi
done
```

## 프로덕션 배포

### 자동 배포 (권장)

배포 스크립트를 사용하여 자동으로 배포합니다:

```bash
# 스크립트 실행 권한 부여 (Linux/Mac)
chmod +x scripts/*.sh

# 배포 실행
./scripts/deploy.sh
```

배포 스크립트는 다음을 자동으로 수행합니다:
- 환경 변수 검증
- Docker 및 Docker Compose 확인
- 기존 데이터베이스 백업
- 최신 코드 Pull (Git 사용 시)
- Docker 이미지 빌드
- 서비스 시작
- 데이터베이스 마이그레이션
- 헬스 체크

### 수동 배포

단계별로 수동 배포를 진행하려면:

#### 1. 데이터베이스 백업

```bash
./scripts/backup-db.sh
```

#### 2. Docker 이미지 빌드

```bash
docker-compose -f docker-compose.prod.yml build
```

#### 3. 서비스 시작

```bash
docker-compose -f docker-compose.prod.yml up -d
```

#### 4. 데이터베이스 마이그레이션

```bash
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

#### 5. 헬스 체크

```bash
./scripts/health-check-prod.sh
```

### 배포 확인

배포가 완료되면 다음 엔드포인트를 확인합니다:

```bash
# Backend API Health Check
curl http://localhost:8000/api/v1/health

# Frontend 접근
curl http://localhost:3000

# Nginx Proxy
curl http://localhost
```

## SSL/TLS 설정

### Let's Encrypt를 사용한 무료 SSL 인증서

#### 1. Certbot 설치

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install certbot python3-certbot-nginx

# CentOS/RHEL
sudo yum install certbot python3-certbot-nginx
```

#### 2. SSL 인증서 발급

```bash
# 도메인을 실제 도메인으로 변경
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

#### 3. nginx.conf 업데이트

`nginx/nginx.conf` 파일에 SSL 설정을 추가합니다:

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # ... 나머지 설정
}
```

#### 4. 인증서 자동 갱신

```bash
# Cron 작업 추가 (매일 자정 갱신 확인)
echo "0 0 * * * root certbot renew --quiet && docker-compose -f /path/to/docker-compose.prod.yml restart nginx" | sudo tee -a /etc/crontab
```

### 자체 서명 인증서 (개발/테스트용)

```bash
# SSL 인증서 디렉토리 생성
mkdir -p nginx/ssl

# 자체 서명 인증서 생성
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/ssl/nginx-selfsigned.key \
  -out nginx/ssl/nginx-selfsigned.crt

# docker-compose.prod.yml 볼륨 마운트 추가
# - ./nginx/ssl:/etc/nginx/ssl:ro
```

## 데이터베이스 관리

### 백업

#### 자동 백업

```bash
# 데이터베이스 백업
./scripts/backup-db.sh
```

백업 파일은 `backups/` 디렉토리에 저장되며, 최근 10개만 유지됩니다.

#### 수동 백업

```bash
# PostgreSQL 덤프
docker-compose -f docker-compose.prod.yml exec db pg_dump -U aura aura > backup_$(date +%Y%m%d).sql

# 압축
gzip backup_$(date +%Y%m%d).sql
```

### 복원

```bash
# 백업에서 복원
gunzip < backups/aura_backup_20240101_120000.sql.gz | \
  docker-compose -f docker-compose.prod.yml exec -T db psql -U aura aura
```

### 마이그레이션

#### 새 마이그레이션 생성

```bash
# Backend 컨테이너 접속
docker-compose -f docker-compose.prod.yml exec backend bash

# Alembic 마이그레이션 생성
alembic revision --autogenerate -m "Description of changes"

# 마이그레이션 적용
alembic upgrade head
```

#### 마이그레이션 롤백

```bash
# 이전 버전으로 롤백
docker-compose -f docker-compose.prod.yml exec backend alembic downgrade -1

# 특정 버전으로 롤백
docker-compose -f docker-compose.prod.yml exec backend alembic downgrade <revision_id>
```

## 모니터링 및 로깅

### 헬스 체크

정기적으로 시스템 상태를 확인합니다:

```bash
# 종합 헬스 체크
./scripts/health-check-prod.sh

# Cron으로 자동 헬스 체크 (5분마다)
echo "*/5 * * * * /path/to/aura/scripts/health-check-prod.sh >> /var/log/aura-health.log 2>&1" | sudo tee -a /etc/crontab
```

### 로그 확인

```bash
# 모든 서비스 로그 (실시간)
docker-compose -f docker-compose.prod.yml logs -f

# 특정 서비스 로그
docker-compose -f docker-compose.prod.yml logs -f backend
docker-compose -f docker-compose.prod.yml logs -f frontend
docker-compose -f docker-compose.prod.yml logs -f nginx
docker-compose -f docker-compose.prod.yml logs -f db

# 마지막 100줄
docker-compose -f docker-compose.prod.yml logs --tail=100 backend

# 에러만 필터링
docker-compose -f docker-compose.prod.yml logs backend | grep -i error
```

### 로그 파일 관리

로그 로테이션 설정 (`/etc/logrotate.d/aura`):

```
/var/lib/docker/containers/*/*.log {
    rotate 7
    daily
    compress
    size=10M
    missingok
    delaycompress
    copytruncate
}
```

### 메트릭 모니터링

```bash
# 컨테이너 리소스 사용량
docker stats

# 특정 컨테이너 상세 정보
docker inspect aura-backend

# 디스크 사용량
df -h

# 데이터베이스 크기
docker-compose -f docker-compose.prod.yml exec db psql -U aura -d aura -c \
  "SELECT pg_size_pretty(pg_database_size('aura'));"
```

## 롤백 절차

### 빠른 롤백

이전 버전으로 신속하게 롤백합니다:

```bash
# 1. 서비스 중지
docker-compose -f docker-compose.prod.yml down

# 2. 이전 코드 버전으로 복원 (Git 사용 시)
git checkout <previous-commit-hash>

# 3. 이미지 재빌드
docker-compose -f docker-compose.prod.yml build

# 4. 서비스 시작
docker-compose -f docker-compose.prod.yml up -d

# 5. 데이터베이스 마이그레이션 롤백 (필요 시)
docker-compose -f docker-compose.prod.yml exec backend alembic downgrade -1
```

### 데이터베이스 롤백

```bash
# 백업에서 복원
docker-compose -f docker-compose.prod.yml down
docker volume rm aura_postgres_data

docker-compose -f docker-compose.prod.yml up -d db
sleep 10

gunzip < backups/aura_backup_YYYYMMDD_HHMMSS.sql.gz | \
  docker-compose -f docker-compose.prod.yml exec -T db psql -U aura aura
```

### 완전한 시스템 초기화

```bash
# 모든 컨테이너 및 볼륨 제거 (주의!)
docker-compose -f docker-compose.prod.yml down -v

# 이미지 제거
docker-compose -f docker-compose.prod.yml down --rmi all

# 재배포
./scripts/deploy.sh
```

## 문제 해결

### 서비스가 시작되지 않음

```bash
# 컨테이너 상태 확인
docker-compose -f docker-compose.prod.yml ps

# 로그 확인
docker-compose -f docker-compose.prod.yml logs

# 특정 컨테이너 재시작
docker-compose -f docker-compose.prod.yml restart backend

# 강제 재생성
docker-compose -f docker-compose.prod.yml up -d --force-recreate
```

### 데이터베이스 연결 실패

```bash
# 데이터베이스 연결 테스트
docker-compose -f docker-compose.prod.yml exec db pg_isready -U aura

# 데이터베이스 로그 확인
docker-compose -f docker-compose.prod.yml logs db

# 환경 변수 확인
docker-compose -f docker-compose.prod.yml exec backend env | grep DATABASE
```

### Playwright 브라우저 실행 실패

```bash
# Backend 컨테이너에 접속
docker-compose -f docker-compose.prod.yml exec backend bash

# Playwright 재설치
playwright install --with-deps chromium

# 컨테이너 재시작
docker-compose -f docker-compose.prod.yml restart backend
```

### 메모리 부족

```bash
# 메모리 사용량 확인
docker stats

# Docker 메모리 제한 증가 (docker-compose.prod.yml)
services:
  backend:
    mem_limit: 2g
  frontend:
    mem_limit: 1g
```

### 디스크 공간 부족

```bash
# 사용하지 않는 Docker 리소스 정리
docker system prune -a

# 오래된 로그 파일 삭제
find /var/lib/docker/containers -name "*.log" -mtime +7 -delete

# 오래된 백업 삭제
find ./backups -name "*.sql.gz" -mtime +30 -delete
```

### API 응답 느림

```bash
# Backend 워커 수 증가 (Dockerfile.prod)
CMD ["gunicorn", "app.main:app", "--workers", "8", "--worker-class", "uvicorn.workers.UvicornWorker"]

# 데이터베이스 연결 풀 설정 (config.py)
# pool_size=20, max_overflow=10

# 컨테이너 재빌드 및 재시작
docker-compose -f docker-compose.prod.yml up -d --build backend
```

## 보안 권장사항

### 1. 방화벽 설정

```bash
# UFW (Ubuntu)
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw deny 8000/tcp  # Backend는 Nginx를 통해서만
sudo ufw deny 3000/tcp  # Frontend는 Nginx를 통해서만
sudo ufw deny 5432/tcp  # PostgreSQL 외부 접근 차단
sudo ufw enable
```

### 2. 정기적인 업데이트

```bash
# 시스템 패키지 업데이트
sudo apt-get update && sudo apt-get upgrade -y

# Docker 이미지 업데이트
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d
```

### 3. 비밀번호 관리

- 모든 기본 비밀번호를 강력한 비밀번호로 변경
- 비밀번호 관리자 사용 (1Password, Bitwarden 등)
- `.env` 파일을 Git에 커밋하지 않음 (`.gitignore` 확인)

### 4. 접근 제어

```bash
# .env 파일 권한 설정
chmod 600 .env

# Docker 소켓 권한
sudo usermod -aG docker $USER
```

## 성능 최적화

### 1. 데이터베이스 최적화

```sql
-- 인덱스 생성
CREATE INDEX idx_analysis_status ON analysis_requests(status);
CREATE INDEX idx_analysis_created ON analysis_requests(created_at);

-- VACUUM 실행
VACUUM ANALYZE;
```

### 2. Nginx 캐싱

```nginx
# nginx.conf에 추가
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=api_cache:10m max_size=100m;

location /api/v1/analysis {
    proxy_cache api_cache;
    proxy_cache_valid 200 5m;
    # ...
}
```

### 3. Docker 이미지 최적화

```bash
# 멀티스테이지 빌드 사용 (이미 적용됨)
# 불필요한 파일 제거
# .dockerignore 활용
```

## 정기 유지보수 체크리스트

### 매일
- [ ] 헬스 체크 실행
- [ ] 에러 로그 검토
- [ ] 리소스 사용량 확인

### 매주
- [ ] 데이터베이스 백업 확인
- [ ] 디스크 공간 확인
- [ ] 보안 업데이트 적용

### 매월
- [ ] 백업 복원 테스트
- [ ] 성능 메트릭 리뷰
- [ ] SSL 인증서 만료일 확인

## 연락처 및 지원

문제가 발생하거나 지원이 필요한 경우:

- GitHub Issues: https://github.com/yourusername/aura/issues
- 문서: https://github.com/yourusername/aura/wiki
- 이메일: support@yourdomain.com

---

**마지막 업데이트**: 2024-01-17
**버전**: 1.0.0
