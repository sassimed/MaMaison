#!/bin/bash
# =============================================================================
# Script de tests MyDar
# Usage: ./run_tests.sh [options]
# Options:
#   --all       Exécuter tous les tests
#   --quick     Tests rapides (health + products)
#   --verbose   Mode verbose
#   --ci        Mode CI (génère rapport JUnit)
# =============================================================================

set -e

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Options par défaut
VERBOSE=""
CI_MODE=""
TEST_PATH="tests/"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --all)
            TEST_PATH="tests/"
            shift
            ;;
        --quick)
            TEST_PATH="tests/test_health.py tests/test_products.py"
            shift
            ;;
        --verbose|-v)
            VERBOSE="-v"
            shift
            ;;
        --ci)
            CI_MODE="--junitxml=test-results.xml"
            shift
            ;;
        *)
            echo "Option inconnue: $1"
            exit 1
            ;;
    esac
done

echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}    MyDar - Tests Unitaires${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""

# Vérifier que pytest est installé
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}pytest n'est pas installé. Installation...${NC}"
    pip install pytest pytest-asyncio httpx
fi

# Aller dans le répertoire backend
cd /app/backend

# Exécuter les tests
echo -e "${GREEN}Exécution des tests...${NC}"
echo ""

if pytest $TEST_PATH $VERBOSE $CI_MODE --tb=short -q; then
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}    ✅ TOUS LES TESTS PASSENT${NC}"
    echo -e "${GREEN}========================================${NC}"
    exit 0
else
    echo ""
    echo -e "${RED}========================================${NC}"
    echo -e "${RED}    ❌ CERTAINS TESTS ONT ÉCHOUÉ${NC}"
    echo -e "${RED}========================================${NC}"
    exit 1
fi
