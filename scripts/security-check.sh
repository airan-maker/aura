#!/bin/bash

# Aura Security Check Script
# Validates security configuration and checks for common vulnerabilities

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "==================================="
echo "Aura Security Check"
echo "==================================="
echo ""

# Track issues
ISSUES=0
WARNINGS=0

# Function to check file exists
check_file() {
    local file=$1
    local name=$2

    echo -n "Checking $name... "
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓ Found${NC}"
        return 0
    else
        echo -e "${RED}✗ Missing${NC}"
        ISSUES=$((ISSUES + 1))
        return 1
    fi
}

# Function to check file permissions
check_permissions() {
    local file=$1
    local expected=$2
    local name=$3

    if [ ! -f "$file" ]; then
        return 1
    fi

    echo -n "Checking $name permissions... "
    if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
        echo -e "${YELLOW}⊘ Skipped (Windows)${NC}"
        return 0
    fi

    actual=$(stat -c "%a" "$file" 2>/dev/null || stat -f "%A" "$file" 2>/dev/null)
    if [ "$actual" -eq "$expected" ] || [ "$actual" -lt "$expected" ]; then
        echo -e "${GREEN}✓ OK ($actual)${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠ Too permissive ($actual, expected $expected)${NC}"
        WARNINGS=$((WARNINGS + 1))
        return 1
    fi
}

# Function to check environment variable
check_env_var() {
    local var=$1
    local name=$2
    local required=${3:-true}

    if [ ! -f .env ]; then
        return 1
    fi

    echo -n "Checking $name... "
    value=$(grep "^$var=" .env | cut -d '=' -f2- | xargs)

    if [ -z "$value" ]; then
        if [ "$required" = true ]; then
            echo -e "${RED}✗ Not set${NC}"
            ISSUES=$((ISSUES + 1))
            return 1
        else
            echo -e "${YELLOW}⚠ Not set (optional)${NC}"
            WARNINGS=$((WARNINGS + 1))
            return 1
        fi
    fi

    # Check for default/weak values
    case "$var" in
        SECRET_KEY)
            if [[ "$value" == *"change"* ]] || [[ "$value" == *"secret"* ]] || [ ${#value} -lt 32 ]; then
                echo -e "${RED}✗ Weak or default value${NC}"
                ISSUES=$((ISSUES + 1))
                return 1
            fi
            ;;
        POSTGRES_PASSWORD)
            if [[ "$value" == *"password"* ]] || [[ "$value" == *"change"* ]] || [ ${#value} -lt 12 ]; then
                echo -e "${RED}✗ Weak password${NC}"
                ISSUES=$((ISSUES + 1))
                return 1
            fi
            ;;
        OPENAI_API_KEY)
            if [[ ! "$value" =~ ^sk- ]]; then
                echo -e "${RED}✗ Invalid format${NC}"
                ISSUES=$((ISSUES + 1))
                return 1
            fi
            ;;
        ALLOWED_ORIGINS)
            if [[ "$value" == *"*"* ]]; then
                echo -e "${YELLOW}⚠ Allows all origins (not recommended for production)${NC}"
                WARNINGS=$((WARNINGS + 1))
                return 1
            fi
            ;;
    esac

    echo -e "${GREEN}✓ OK${NC}"
    return 0
}

# 1. File Checks
echo -e "${BLUE}[1/6] Configuration Files${NC}"
echo "-----------------------------------"
check_file ".env" ".env file"
check_file ".dockerignore" ".dockerignore file"
check_file "docker-compose.prod.yml" "Production Docker Compose"
check_file "backend/Dockerfile.prod" "Backend Production Dockerfile"
check_file "frontend/Dockerfile.prod" "Frontend Production Dockerfile"
check_file "nginx/nginx.conf" "Nginx configuration"
echo ""

# 2. File Permissions
echo -e "${BLUE}[2/6] File Permissions${NC}"
echo "-----------------------------------"
if [ -f .env ]; then
    check_permissions ".env" 600 ".env file"
fi
if [ -d nginx/ssl ]; then
    for key in nginx/ssl/*.key; do
        if [ -f "$key" ]; then
            check_permissions "$key" 600 "SSL private key"
        fi
    done
fi
echo ""

# 3. Environment Variables
echo -e "${BLUE}[3/6] Environment Variables${NC}"
echo "-----------------------------------"
if [ -f .env ]; then
    source .env
    check_env_var "OPENAI_API_KEY" "OpenAI API key"
    check_env_var "SECRET_KEY" "Secret key"
    check_env_var "POSTGRES_PASSWORD" "Database password"
    check_env_var "ALLOWED_ORIGINS" "CORS origins"
    check_env_var "ENVIRONMENT" "Environment" false
    check_env_var "LOG_LEVEL" "Log level" false
else
    echo -e "${RED}✗ .env file not found${NC}"
    ISSUES=$((ISSUES + 1))
fi
echo ""

# 4. Docker Security
echo -e "${BLUE}[4/6] Docker Configuration${NC}"
echo "-----------------------------------"

echo -n "Checking non-root user in backend Dockerfile... "
if grep -q "USER aura" backend/Dockerfile.prod 2>/dev/null; then
    echo -e "${GREEN}✓ OK${NC}"
else
    echo -e "${RED}✗ Running as root${NC}"
    ISSUES=$((ISSUES + 1))
fi

echo -n "Checking non-root user in frontend Dockerfile... "
if grep -q "USER nextjs" frontend/Dockerfile.prod 2>/dev/null; then
    echo -e "${GREEN}✓ OK${NC}"
else
    echo -e "${RED}✗ Running as root${NC}"
    ISSUES=$((ISSUES + 1))
fi

echo -n "Checking .dockerignore for .env... "
if grep -q "^\.env$" .dockerignore 2>/dev/null; then
    echo -e "${GREEN}✓ OK${NC}"
else
    echo -e "${RED}✗ .env not ignored${NC}"
    ISSUES=$((ISSUES + 1))
fi

echo ""

# 5. Security Middleware
echo -e "${BLUE}[5/6] Security Middleware${NC}"
echo "-----------------------------------"

echo -n "Checking SecurityHeadersMiddleware... "
if grep -q "SecurityHeadersMiddleware" backend/app/main.py 2>/dev/null; then
    echo -e "${GREEN}✓ Configured${NC}"
else
    echo -e "${RED}✗ Not found${NC}"
    ISSUES=$((ISSUES + 1))
fi

echo -n "Checking RateLimitMiddleware... "
if grep -q "RateLimitMiddleware" backend/app/main.py 2>/dev/null; then
    echo -e "${GREEN}✓ Configured${NC}"
else
    echo -e "${RED}✗ Not found${NC}"
    ISSUES=$((ISSUES + 1))
fi

echo -n "Checking URLValidationMiddleware... "
if grep -q "URLValidationMiddleware" backend/app/main.py 2>/dev/null; then
    echo -e "${GREEN}✓ Configured${NC}"
else
    echo -e "${RED}✗ Not found${NC}"
    ISSUES=$((ISSUES + 1))
fi

echo ""

# 6. Dependency Security
echo -e "${BLUE}[6/6] Dependency Security${NC}"
echo "-----------------------------------"

# Check for outdated Python packages
echo "Checking Python dependencies..."
if [ -f backend/requirements.txt ]; then
    if command -v pip &> /dev/null; then
        cd backend 2>/dev/null || true
        outdated=$(pip list --outdated --format=columns 2>/dev/null | tail -n +3 | wc -l)
        cd .. 2>/dev/null || true
        if [ "$outdated" -gt 0 ]; then
            echo -e "${YELLOW}⚠ $outdated outdated packages${NC}"
            WARNINGS=$((WARNINGS + 1))
        else
            echo -e "${GREEN}✓ All packages up to date${NC}"
        fi
    else
        echo -e "${YELLOW}⊘ pip not found, skipping${NC}"
    fi
else
    echo -e "${RED}✗ requirements.txt not found${NC}"
    ISSUES=$((ISSUES + 1))
fi

# Check for npm vulnerabilities
echo "Checking Node.js dependencies..."
if [ -f frontend/package.json ]; then
    if command -v npm &> /dev/null; then
        cd frontend
        npm_audit=$(npm audit --json 2>/dev/null || echo '{"vulnerabilities":{}}')
        cd ..
        vulnerabilities=$(echo "$npm_audit" | grep -o '"vulnerabilities"' | wc -l)
        if [ "$vulnerabilities" -gt 0 ]; then
            echo -e "${YELLOW}⚠ npm audit found issues${NC}"
            WARNINGS=$((WARNINGS + 1))
        else
            echo -e "${GREEN}✓ No known vulnerabilities${NC}"
        fi
    else
        echo -e "${YELLOW}⊘ npm not found, skipping${NC}"
    fi
else
    echo -e "${RED}✗ package.json not found${NC}"
    ISSUES=$((ISSUES + 1))
fi

echo ""

# Summary
echo "==================================="
echo "Summary"
echo "==================================="
echo -e "Critical Issues: ${RED}$ISSUES${NC}"
echo -e "Warnings: ${YELLOW}$WARNINGS${NC}"
echo ""

if [ $ISSUES -gt 0 ]; then
    echo -e "${RED}✗ Security check failed!${NC}"
    echo "Please fix the critical issues before deploying."
    exit 1
elif [ $WARNINGS -gt 0 ]; then
    echo -e "${YELLOW}⚠ Security check passed with warnings${NC}"
    echo "Consider addressing the warnings for better security."
    exit 0
else
    echo -e "${GREEN}✓ All security checks passed!${NC}"
    exit 0
fi
