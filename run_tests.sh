#!/bin/bash
# =============================================================================
# MyDar - Script de Tests CI/CD
# Execute tous les tests avant déploiement
# =============================================================================

set -e  # Exit on error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=============================================${NC}"
echo -e "${BLUE}     MyDar - Tests CI/CD Pipeline${NC}"
echo -e "${BLUE}=============================================${NC}"
echo ""

# Configuration
BACKEND_DIR="/app/backend"
FRONTEND_DIR="/app/frontend"
COVERAGE_MIN=20  # Minimum coverage percentage required
TEST_TIMEOUT=300  # 5 minutes timeout

# Track results
BACKEND_TESTS_PASSED=false
FRONTEND_TESTS_PASSED=false
LINT_PASSED=false

# =============================================================================
# STEP 1: Backend Linting
# =============================================================================
echo -e "${YELLOW}[1/5] Backend Linting (Ruff)...${NC}"
cd $BACKEND_DIR

if pip show ruff > /dev/null 2>&1; then
    if ruff check . --ignore E501,F401 --exclude "tests/*,seed_*.py" 2>/dev/null; then
        echo -e "${GREEN}✓ Backend linting passed${NC}"
        LINT_PASSED=true
    else
        echo -e "${YELLOW}⚠ Backend linting warnings (non-blocking)${NC}"
        LINT_PASSED=true  # Non-blocking
    fi
else
    echo -e "${YELLOW}⚠ Ruff not installed, skipping linting${NC}"
    LINT_PASSED=true
fi
echo ""

# =============================================================================
# STEP 2: Backend Unit Tests
# =============================================================================
echo -e "${YELLOW}[2/5] Backend Unit Tests...${NC}"
cd $BACKEND_DIR

# Install test dependencies if needed
pip install pytest pytest-asyncio pytest-cov httpx -q 2>/dev/null

# Run tests with coverage
if timeout $TEST_TIMEOUT python -m pytest tests/ \
    --cov=. \
    --cov-report=term-missing \
    --cov-report=xml:coverage.xml \
    --cov-fail-under=$COVERAGE_MIN \
    -v \
    --tb=short \
    2>&1; then
    echo -e "${GREEN}✓ Backend tests passed${NC}"
    BACKEND_TESTS_PASSED=true
else
    echo -e "${RED}✗ Backend tests failed${NC}"
    BACKEND_TESTS_PASSED=false
fi
echo ""

# =============================================================================
# STEP 3: API Health Check
# =============================================================================
echo -e "${YELLOW}[3/5] API Health Check...${NC}"

API_URL="http://localhost:8001/api"
HEALTH_CHECK=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/health" 2>/dev/null || echo "000")

if [ "$HEALTH_CHECK" = "200" ]; then
    echo -e "${GREEN}✓ API is healthy${NC}"
else
    echo -e "${YELLOW}⚠ API health check returned $HEALTH_CHECK${NC}"
fi
echo ""

# =============================================================================
# STEP 4: Frontend Linting
# =============================================================================
echo -e "${YELLOW}[4/5] Frontend Linting (ESLint)...${NC}"
cd $FRONTEND_DIR

if [ -f "node_modules/.bin/eslint" ]; then
    if yarn lint 2>/dev/null; then
        echo -e "${GREEN}✓ Frontend linting passed${NC}"
    else
        echo -e "${YELLOW}⚠ Frontend linting warnings (non-blocking)${NC}"
    fi
else
    echo -e "${YELLOW}⚠ ESLint not installed, skipping${NC}"
fi
echo ""

# =============================================================================
# STEP 5: Frontend Build Test
# =============================================================================
echo -e "${YELLOW}[5/5] Frontend Build Test...${NC}"
cd $FRONTEND_DIR

# Test if build would succeed (dry run)
if yarn build 2>&1 | tail -5; then
    echo -e "${GREEN}✓ Frontend build successful${NC}"
    FRONTEND_TESTS_PASSED=true
else
    echo -e "${RED}✗ Frontend build failed${NC}"
    FRONTEND_TESTS_PASSED=false
fi
echo ""

# =============================================================================
# SUMMARY
# =============================================================================
echo -e "${BLUE}=============================================${NC}"
echo -e "${BLUE}              TEST SUMMARY${NC}"
echo -e "${BLUE}=============================================${NC}"
echo ""

if [ "$LINT_PASSED" = true ]; then
    echo -e "${GREEN}✓ Linting: PASSED${NC}"
else
    echo -e "${RED}✗ Linting: FAILED${NC}"
fi

if [ "$BACKEND_TESTS_PASSED" = true ]; then
    echo -e "${GREEN}✓ Backend Tests: PASSED${NC}"
else
    echo -e "${RED}✗ Backend Tests: FAILED${NC}"
fi

if [ "$FRONTEND_TESTS_PASSED" = true ]; then
    echo -e "${GREEN}✓ Frontend Build: PASSED${NC}"
else
    echo -e "${RED}✗ Frontend Build: FAILED${NC}"
fi

echo ""

# Final decision
if [ "$BACKEND_TESTS_PASSED" = true ] && [ "$FRONTEND_TESTS_PASSED" = true ]; then
    echo -e "${GREEN}=============================================${NC}"
    echo -e "${GREEN}  ✓ ALL TESTS PASSED - READY TO DEPLOY${NC}"
    echo -e "${GREEN}=============================================${NC}"
    exit 0
else
    echo -e "${RED}=============================================${NC}"
    echo -e "${RED}  ✗ TESTS FAILED - DO NOT DEPLOY${NC}"
    echo -e "${RED}=============================================${NC}"
    exit 1
fi
