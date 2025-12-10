#!/bin/bash
# Deployment Verification Script
# Checks security headers and health endpoints on production deployments

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
FRONTEND_URL="${FRONTEND_URL:-https://dashti.se}"
BACKEND_URL="${BACKEND_URL:-https://dashti-portfolio-backend.fly.dev}"

echo "========================================"
echo "Deployment Verification Script"
echo "========================================"
echo ""
echo "Frontend: $FRONTEND_URL"
echo "Backend:  $BACKEND_URL"
echo ""

# Track failures
FAILURES=0

# Function to check a header
check_header() {
    local url="$1"
    local header="$2"
    local expected="$3"
    local headers_output="$4"

    local value=$(echo "$headers_output" | grep -i "^$header:" | cut -d: -f2- | tr -d ' \r')

    if [ -z "$value" ]; then
        echo -e "  ${RED}[FAIL]${NC} $header: MISSING"
        return 1
    elif [ -n "$expected" ] && [ "$value" != "$expected" ]; then
        echo -e "  ${YELLOW}[WARN]${NC} $header: $value (expected: $expected)"
        return 0
    else
        echo -e "  ${GREEN}[OK]${NC} $header: $value"
        return 0
    fi
}

# Function to check endpoint health
check_health() {
    local url="$1"
    local name="$2"

    echo "Checking $name health..."

    local response=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null)

    if [ "$response" = "200" ]; then
        echo -e "  ${GREEN}[OK]${NC} $name is healthy (HTTP $response)"
        return 0
    else
        echo -e "  ${RED}[FAIL]${NC} $name returned HTTP $response"
        return 1
    fi
}

# Function to verify security headers
verify_security_headers() {
    local url="$1"
    local name="$2"

    echo ""
    echo "Checking $name security headers..."
    echo "URL: $url"
    echo ""

    local headers=$(curl -sI "$url" 2>/dev/null)

    if [ -z "$headers" ]; then
        echo -e "  ${RED}[FAIL]${NC} Could not fetch headers from $url"
        return 1
    fi

    local failed=0

    # Required security headers
    check_header "$url" "X-Content-Type-Options" "nosniff" "$headers" || ((failed++))
    check_header "$url" "X-Frame-Options" "DENY" "$headers" || ((failed++))
    check_header "$url" "X-XSS-Protection" "" "$headers" || ((failed++))
    check_header "$url" "Referrer-Policy" "" "$headers" || ((failed++))
    check_header "$url" "Permissions-Policy" "" "$headers" || ((failed++))

    # HSTS (only for HTTPS)
    if [[ "$url" == https://* ]]; then
        check_header "$url" "Strict-Transport-Security" "" "$headers" || ((failed++))
    fi

    # Content-Security-Policy (warning only)
    local csp=$(echo "$headers" | grep -i "^Content-Security-Policy:" | cut -d: -f2-)
    if [ -n "$csp" ]; then
        echo -e "  ${GREEN}[OK]${NC} Content-Security-Policy: present"
    else
        echo -e "  ${YELLOW}[WARN]${NC} Content-Security-Policy: not set"
    fi

    return $failed
}

# Check Backend Health
echo ""
echo "========================================"
echo "1. Backend Health Checks"
echo "========================================"

check_health "$BACKEND_URL/api/v1/health" "Backend /health" || ((FAILURES++))
check_health "$BACKEND_URL/api/v1/health/ready" "Backend /health/ready" || ((FAILURES++))
check_health "$BACKEND_URL/api/v1/health/live" "Backend /health/live" || ((FAILURES++))

# Check Frontend Health
echo ""
echo "========================================"
echo "2. Frontend Health Check"
echo "========================================"

check_health "$FRONTEND_URL" "Frontend" || ((FAILURES++))

# Check Backend Security Headers
echo ""
echo "========================================"
echo "3. Backend Security Headers"
echo "========================================"

verify_security_headers "$BACKEND_URL/api/v1/health" "Backend" || ((FAILURES++))

# Check Frontend Security Headers
echo ""
echo "========================================"
echo "4. Frontend Security Headers"
echo "========================================"

verify_security_headers "$FRONTEND_URL" "Frontend" || ((FAILURES++))

# API Response Check
echo ""
echo "========================================"
echo "5. API Response Validation"
echo "========================================"

echo "Checking API root endpoint..."
api_response=$(curl -s "$BACKEND_URL/" 2>/dev/null)
if echo "$api_response" | grep -q "Portfolio API"; then
    echo -e "  ${GREEN}[OK]${NC} API returns expected response"
else
    echo -e "  ${RED}[FAIL]${NC} Unexpected API response"
    ((FAILURES++))
fi

# SSL Certificate Check
echo ""
echo "========================================"
echo "6. SSL Certificate Check"
echo "========================================"

for url in "$FRONTEND_URL" "$BACKEND_URL"; do
    echo "Checking SSL for $url..."
    domain=$(echo "$url" | sed 's|https://||' | cut -d/ -f1)

    expiry=$(echo | openssl s_client -servername "$domain" -connect "$domain:443" 2>/dev/null | openssl x509 -noout -dates 2>/dev/null | grep "notAfter" | cut -d= -f2)

    if [ -n "$expiry" ]; then
        echo -e "  ${GREEN}[OK]${NC} SSL valid until: $expiry"
    else
        echo -e "  ${YELLOW}[WARN]${NC} Could not verify SSL certificate"
    fi
done

# Summary
echo ""
echo "========================================"
echo "Summary"
echo "========================================"

if [ $FAILURES -eq 0 ]; then
    echo -e "${GREEN}All checks passed!${NC}"
    exit 0
else
    echo -e "${RED}$FAILURES check(s) failed${NC}"
    exit 1
fi
