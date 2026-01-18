# Security Guidelines

This document outlines security best practices and implemented security measures for the Aura platform.

## Table of Contents

1. [Security Features](#security-features)
2. [Deployment Security](#deployment-security)
3. [API Security](#api-security)
4. [Database Security](#database-security)
5. [SSRF Protection](#ssrf-protection)
6. [Rate Limiting](#rate-limiting)
7. [Security Headers](#security-headers)
8. [Secrets Management](#secrets-management)
9. [Security Checklist](#security-checklist)
10. [Reporting Vulnerabilities](#reporting-vulnerabilities)

## Security Features

### Implemented Security Measures

1. **HTTPS/TLS Encryption**
   - SSL/TLS support via Nginx
   - Automatic HTTP to HTTPS redirect
   - Strong cipher suites (TLSv1.2+)

2. **Security Headers**
   - X-Content-Type-Options: nosniff
   - X-Frame-Options: DENY
   - X-XSS-Protection: 1; mode=block
   - Strict-Transport-Security (HSTS)
   - Content-Security-Policy (CSP)
   - Referrer-Policy

3. **Rate Limiting**
   - API endpoint rate limiting (60 req/min per IP)
   - Burst protection (100 req/10sec)
   - Nginx-level rate limiting

4. **SSRF Protection**
   - URL validation middleware
   - Blocked private IP ranges
   - Blocked cloud metadata endpoints

5. **Input Validation**
   - Pydantic schema validation
   - URL format validation
   - Request size limits

## Deployment Security

### Environment Variables

**Never commit sensitive data to Git:**

```bash
# Bad - Don't do this
echo "OPENAI_API_KEY=sk-real-key-here" >> .env.production

# Good - Use secure vaults or environment-specific configs
export OPENAI_API_KEY=$(cat /secure/vault/openai-key)
```

**Use strong secret keys:**

```bash
# Generate strong SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

### Docker Security

**Run containers as non-root user:**

```dockerfile
# Already implemented in Dockerfile.prod
RUN useradd -m -u 1000 aura
USER aura
```

**Limit container resources:**

```yaml
# docker-compose.prod.yml
services:
  backend:
    mem_limit: 2g
    cpus: 2.0
    pids_limit: 100
```

### File Permissions

```bash
# Restrict .env file access
chmod 600 .env

# Restrict SSL certificates
chmod 600 nginx/ssl/*.key
chmod 644 nginx/ssl/*.crt
```

## API Security

### Authentication (Future Enhancement)

For production with multiple users, implement authentication:

```python
# Example JWT authentication (not yet implemented)
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer

security = HTTPBearer()

async def verify_token(credentials = Depends(security)):
    # Verify JWT token
    pass
```

### CORS Configuration

**Production CORS settings:**

```python
# backend/app/config.py
ALLOWED_ORIGINS = ["https://yourdomain.com", "https://www.yourdomain.com"]

# NOT recommended for production
ALLOWED_ORIGINS = ["*"]  # Don't use this!
```

### Input Validation

**All endpoints use Pydantic for validation:**

```python
from pydantic import BaseModel, HttpUrl

class AnalysisRequest(BaseModel):
    url: HttpUrl  # Automatically validates URL format
```

## Database Security

### Connection Security

**Use strong passwords:**

```bash
# Generate strong database password
openssl rand -base64 32
```

**Restrict database access:**

```yaml
# docker-compose.prod.yml
services:
  db:
    ports:
      - "127.0.0.1:5432:5432"  # Bind to localhost only
```

### SQL Injection Prevention

**Using SQLAlchemy ORM (prevents SQL injection):**

```python
# Safe - Parameterized query
result = await db.execute(
    select(AnalysisRequest).where(AnalysisRequest.id == request_id)
)

# Unsafe - Don't do this
result = await db.execute(f"SELECT * FROM analysis WHERE id = '{request_id}'")
```

### Data Encryption

**Encrypt sensitive data at rest (if needed):**

```python
from cryptography.fernet import Fernet

# Example: Encrypt API keys in database
def encrypt_api_key(key: str) -> bytes:
    f = Fernet(settings.ENCRYPTION_KEY)
    return f.encrypt(key.encode())
```

## SSRF Protection

### URL Validation

The `URLValidationMiddleware` prevents SSRF attacks by blocking:

1. **Private IP addresses:**
   - 10.0.0.0/8
   - 172.16.0.0/12
   - 192.168.0.0/16
   - 127.0.0.0/8 (localhost)

2. **Cloud metadata endpoints:**
   - 169.254.169.254 (AWS)
   - metadata.google.internal (GCP)

3. **Link-local addresses:**
   - ::1 (IPv6 localhost)
   - fe80::/10 (IPv6 link-local)

### Implementation

```python
# backend/app/middleware/security.py
BLOCKED_HOSTS = {
    "localhost",
    "127.0.0.1",
    "169.254.169.254",
    # ...
}

BLOCKED_NETWORKS = [
    "10.",
    "172.16.",
    "192.168.",
    # ...
]
```

### Testing SSRF Protection

```bash
# These should be blocked
curl -X POST http://localhost:8000/api/v1/analysis \
  -H "Content-Type: application/json" \
  -d '{"url": "http://localhost:8080"}'

curl -X POST http://localhost:8000/api/v1/analysis \
  -H "Content-Type: application/json" \
  -d '{"url": "http://169.254.169.254/latest/meta-data"}'
```

## Rate Limiting

### Application-Level Rate Limiting

**Current limits:**
- 60 requests per minute per IP
- 100 requests per 10 seconds (burst protection)

**Customize in `main.py`:**

```python
from app.middleware.security import RateLimitMiddleware

app.add_middleware(
    RateLimitMiddleware,
    requests_per_minute=60,
    burst_size=100
)
```

### Nginx Rate Limiting

**nginx.conf configuration:**

```nginx
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
limit_req_zone $binary_remote_addr zone=general_limit:10m rate=100r/s;

location /api/ {
    limit_req zone=api_limit burst=20 nodelay;
}
```

### Rate Limit Response

```http
HTTP/1.1 429 Too Many Requests
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1641024000
Retry-After: 60

{
  "detail": "Too many requests. Please try again later."
}
```

## Security Headers

### HTTP Security Headers

**Applied via SecurityHeadersMiddleware:**

```python
response.headers["X-Content-Type-Options"] = "nosniff"
response.headers["X-Frame-Options"] = "DENY"
response.headers["X-XSS-Protection"] = "1; mode=block"
response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
```

### Content Security Policy

```http
Content-Security-Policy:
  default-src 'self';
  script-src 'self' 'unsafe-inline' 'unsafe-eval';
  style-src 'self' 'unsafe-inline';
  img-src 'self' data: https:;
  font-src 'self' data:;
  connect-src 'self';
  frame-ancestors 'none';
```

### Testing Security Headers

```bash
# Check security headers
curl -I https://yourdomain.com/api/v1/health

# Use online tools
# https://securityheaders.com
# https://observatory.mozilla.org
```

## Secrets Management

### Environment Variables

**Development (.env):**

```bash
# Use weak credentials for local development only
POSTGRES_PASSWORD=dev_password
SECRET_KEY=dev_secret_key
```

**Production:**

```bash
# Use strong, randomly generated secrets
POSTGRES_PASSWORD=$(openssl rand -base64 32)
SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(64))")
```

### Secrets Vault (Recommended for Production)

Use a secrets management service:

- **AWS Secrets Manager**
- **HashiCorp Vault**
- **Azure Key Vault**
- **Google Secret Manager**

**Example with AWS Secrets Manager:**

```python
import boto3

def get_secret(secret_name):
    client = boto3.client('secretsmanager')
    response = client.get_secret_value(SecretId=secret_name)
    return response['SecretString']

# In config.py
OPENAI_API_KEY = get_secret('aura/openai-api-key')
```

### .gitignore

**Ensure these are ignored:**

```gitignore
.env
.env.*
!.env.example

# SSL certificates
*.key
*.pem
*.crt

# Backups (may contain sensitive data)
backups/
*.sql
*.sql.gz
```

## Security Checklist

### Pre-Deployment Checklist

- [ ] Change all default passwords
- [ ] Generate strong SECRET_KEY
- [ ] Configure ALLOWED_ORIGINS for production domain
- [ ] Set up SSL/TLS certificates
- [ ] Configure firewall rules
- [ ] Enable HTTPS redirect
- [ ] Restrict database access to localhost
- [ ] Review and update security headers
- [ ] Test rate limiting
- [ ] Test SSRF protection
- [ ] Disable API docs in production (ENVIRONMENT=production)
- [ ] Set up log monitoring
- [ ] Configure automated backups
- [ ] Test backup restoration
- [ ] Review file permissions (.env, SSL certs)
- [ ] Update dependencies to latest secure versions

### Regular Security Maintenance

**Weekly:**
- [ ] Review security logs for suspicious activity
- [ ] Check for failed authentication attempts
- [ ] Monitor rate limit violations

**Monthly:**
- [ ] Update all dependencies
- [ ] Review access logs
- [ ] Test backup restoration
- [ ] Scan for vulnerabilities

**Quarterly:**
- [ ] Penetration testing
- [ ] Security audit
- [ ] Review and update security policies

### Dependency Security

**Check for vulnerabilities:**

```bash
# Python backend
cd backend
pip install safety
safety check

# Node.js frontend
cd frontend
npm audit
npm audit fix
```

**Update dependencies:**

```bash
# Backend
pip list --outdated
pip install --upgrade <package>

# Frontend
npm outdated
npm update
```

## Reporting Vulnerabilities

### Responsible Disclosure

If you discover a security vulnerability, please report it to:

**Email:** security@yourdomain.com

**Please include:**
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

**We commit to:**
- Acknowledge receipt within 24 hours
- Provide status update within 7 days
- Credit researchers (if desired)

### Bug Bounty Program

Currently, we do not have a formal bug bounty program. However, we appreciate security researchers who responsibly disclose vulnerabilities.

## Additional Resources

### Security Tools

- **OWASP ZAP** - Web application security scanner
- **Burp Suite** - Web vulnerability scanner
- **nmap** - Network security scanner
- **Trivy** - Container vulnerability scanner

### Security Standards

- **OWASP Top 10** - https://owasp.org/www-project-top-ten/
- **CWE Top 25** - https://cwe.mitre.org/top25/
- **NIST Guidelines** - https://www.nist.gov/cybersecurity

### Testing Commands

```bash
# Scan Docker images for vulnerabilities
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy image aura-backend:latest

# Test SSL configuration
testssl.sh https://yourdomain.com

# Security headers check
curl -I https://yourdomain.com | grep -E "^(X-|Strict|Content-Security)"
```

---

**Last Updated:** 2024-01-17
**Version:** 1.0.0
**Maintained by:** Aura Security Team
