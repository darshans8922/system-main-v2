#!/usr/bin/env bash
set -euo pipefail

BASE_URL="https://system-main-v2.onrender.com"
TEST_USER="bharat"
TEST_CODE="RENDER-SMOKE-$(date +%s)"

echo "1) Health check..."
curl -sf "$BASE_URL/health" | jq .

echo "2) Username verify..."
curl -sf "$BASE_URL/api/users/$TEST_USER/verify" | jq .

echo "3) Send test code..."
curl -sf -X POST "$BASE_URL/api/ingest" \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"$TEST_USER\",\"code\":\"$TEST_CODE\",\"source\":\"smoke\"}" \
  | jq .

echo "Smoke test complete."