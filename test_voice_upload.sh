#!/bin/bash
# Test script for voice upload API (Question-Wise Only)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

API_URL="http://localhost:8000/api/v1"

echo -e "${YELLOW}=== Voice Upload API Test Script (Question-Wise) ===${NC}\n"

# Step 1: Login to get token
echo -e "${YELLOW}Step 1: Login to get JWT token...${NC}"
read -p "Username: " USERNAME
read -sp "Password: " PASSWORD
echo ""

LOGIN_RESPONSE=$(curl -s -X POST "$API_URL/auth/login/" \
  -H "Content-Type: application/json" \
  -d "{\"username\": \"$USERNAME\", \"password\": \"$PASSWORD\"}")

ACCESS_TOKEN=$(echo $LOGIN_RESPONSE | grep -o '"access":"[^"]*' | cut -d'"' -f4)

if [ -z "$ACCESS_TOKEN" ]; then
  echo -e "${RED}❌ Login failed!${NC}"
  echo "Response: $LOGIN_RESPONSE"
  exit 1
fi

echo -e "${GREEN}✓ Login successful!${NC}"
echo "Access token: ${ACCESS_TOKEN:0:50}..."
echo ""

# Step 2: Test upload with token (should work)
echo -e "${YELLOW}Step 2: Test voice upload WITH token (should succeed)...${NC}"

# Create a test audio file if it doesn't exist
if [ ! -f "test_audio.webm" ]; then
  echo "Creating test audio file..."
  # Create empty webm file (for testing only)
  touch test_audio.webm
fi

UPLOAD_RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" -X POST "$API_URL/voice/upload/" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -F "audio_file=@test_audio.webm" \
  -F "live_transcript=update question 3 as 8 marks" \
  -F "context_class=1" \
  -F "context_section=B" \
  -F "context_roll_number=14" \
  -F "context_subject_id=1")

HTTP_STATUS=$(echo "$UPLOAD_RESPONSE" | grep -o 'HTTP_STATUS:[0-9]*' | cut -d':' -f2)
RESPONSE_BODY=$(echo "$UPLOAD_RESPONSE" | sed 's/HTTP_STATUS:[0-9]*$//')

if [ "$HTTP_STATUS" = "200" ]; then
  echo -e "${GREEN}✓ Upload successful! (HTTP 200)${NC}"
  echo "Response: $RESPONSE_BODY" | python -m json.tool 2>/dev/null || echo "$RESPONSE_BODY"
else
  echo -e "${RED}❌ Upload failed! (HTTP $HTTP_STATUS)${NC}"
  echo "Response: $RESPONSE_BODY"
fi
echo ""

# Step 3: Test upload without token (should fail with 401)
echo -e "${YELLOW}Step 3: Test voice upload WITHOUT token (should fail with 401)...${NC}"

UNAUTH_RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" -X POST "$API_URL/voice/upload/" \
  -F "audio_file=@test_audio.webm")

HTTP_STATUS=$(echo "$UNAUTH_RESPONSE" | grep -o 'HTTP_STATUS:[0-9]*' | cut -d':' -f2)
RESPONSE_BODY=$(echo "$UNAUTH_RESPONSE" | sed 's/HTTP_STATUS:[0-9]*$//')

if [ "$HTTP_STATUS" = "401" ]; then
  echo -e "${GREEN}✓ Correctly rejected! (HTTP 401)${NC}"
  echo "Response: $RESPONSE_BODY"
else
  echo -e "${RED}❌ Unexpected status! (HTTP $HTTP_STATUS)${NC}"
  echo "Response: $RESPONSE_BODY"
fi
echo ""

# Step 4: Test upload without file (should fail with 400)
echo -e "${YELLOW}Step 4: Test voice upload WITHOUT file (should fail with 400)...${NC}"

NOFILE_RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" -X POST "$API_URL/voice/upload/" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -F "live_transcript=test")

HTTP_STATUS=$(echo "$NOFILE_RESPONSE" | grep -o 'HTTP_STATUS:[0-9]*' | cut -d':' -f2)
RESPONSE_BODY=$(echo "$NOFILE_RESPONSE" | sed 's/HTTP_STATUS:[0-9]*$//')

if [ "$HTTP_STATUS" = "400" ]; then
  echo -e "${GREEN}✓ Correctly rejected! (HTTP 400)${NC}"
  echo "Response: $RESPONSE_BODY"
else
  echo -e "${RED}❌ Unexpected status! (HTTP $HTTP_STATUS)${NC}"
  echo "Response: $RESPONSE_BODY"
fi
echo ""

echo -e "${GREEN}=== Test Complete ===${NC}"
echo -e "${YELLOW}Summary:${NC}"
echo "- Login: ✓"
echo "- Upload with token: Check above"
echo "- Upload without token: Should be 401"
echo "- Upload without file: Should be 400"
