#!/bin/bash

# Pre-push security verification script
# Run this before pushing to public GitHub repository

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║       SECURITY VERIFICATION - BEFORE GITHUB PUSH             ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

FAILED=0

# Test 1: Check for exposed API keys in git history
echo "1. Checking for exposed API keys in git history..."
if git log -p --all | grep -q -E "GOOGLE_API_KEY=[A-Za-z0-9_-]{20,}|sk-[A-Za-z0-9_-]{20,}|AIza[A-Za-z0-9_-]{10,}|lsv2_pt_[A-Za-z0-9]"; then
    echo -e "   ${RED}✗ FAILED${NC} - Found exposed API keys in history!"
    FAILED=1
else
    echo -e "   ${GREEN}✓ PASS${NC} - No exposed API keys found"
fi

# Test 2: Verify .env file is in .gitignore
echo ""
echo "2. Verifying .env is in .gitignore..."
if grep -q "^\.env$" .gitignore; then
    echo -e "   ${GREEN}✓ PASS${NC} - .env properly excluded"
else
    echo -e "   ${RED}✗ FAILED${NC} - .env not in .gitignore"
    FAILED=1
fi

# Test 3: Check for .env files in git
echo ""
echo "3. Checking for .env files in git..."
if git ls-files | grep -q "\.env\$\|\.env\.\|\.env-"; then
    echo -e "   ${RED}✗ FAILED${NC} - Found .env files in git:"
    git ls-files | grep "\.env"
    FAILED=1
else
    echo -e "   ${GREEN}✓ PASS${NC} - No .env files in git (only .env.example allowed)"
fi

# Test 4: Verify only .env.example exists
echo ""
echo "4. Checking tracked environment files..."
ENV_FILES=$(git ls-files | grep "\.env")
if [ "$ENV_FILES" = ".env.example" ]; then
    echo -e "   ${GREEN}✓ PASS${NC} - Only .env.example is tracked (safe template)"
else
    echo -e "   ${RED}✗ FAILED${NC} - Unexpected env files tracked:"
    echo "$ENV_FILES"
    FAILED=1
fi

# Test 5: Verify .env.example is safe
echo ""
echo "5. Checking .env.example for real secrets..."
if grep -q -E "=[A-Za-z0-9_-]{20,}|sk-|AIza|lsv2_pt" .env.example; then
    echo -e "   ${RED}✗ FAILED${NC} - .env.example contains real secrets!"
    FAILED=1
else
    echo -e "   ${GREEN}✓ PASS${NC} - .env.example uses only placeholders"
fi

# Test 6: Check for commented-out API keys
echo ""
echo "6. Checking for commented-out API keys in code..."
if git log -p --all | grep -q -E "^[+-].*#.*GOOGLE_API_KEY=[A-Za-z0-9_-]{20,}|^[+-].*#.*sk-"; then
    echo -e "   ${YELLOW}⚠ WARNING${NC} - Found commented API keys (double-check manually)"
else
    echo -e "   ${GREEN}✓ PASS${NC} - No commented API keys found"
fi

# Test 7: Verify git status is clean
echo ""
echo "7. Checking git status..."
if git status --porcelain | grep -q "^\?\? \.env$\|^\?\? \.env\."; then
    echo -e "   ${YELLOW}⚠ WARNING${NC} - Untracked .env files in working directory (OK if gitignored)"
else
    echo -e "   ${GREEN}✓ PASS${NC} - No untracked secrets in working directory"
fi

# Summary
echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
if [ $FAILED -eq 0 ]; then
    echo -e "║ ${GREEN}✓ ALL CHECKS PASSED - SAFE TO PUSH TO GITHUB${NC}       ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    exit 0
else
    echo -e "║ ${RED}✗ SOME CHECKS FAILED - DO NOT PUSH${NC}                ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    exit 1
fi
