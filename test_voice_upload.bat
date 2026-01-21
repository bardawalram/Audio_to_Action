@echo off
REM Test script for voice upload API (Question-Wise Only)

echo === Voice Upload API Test Script (Question-Wise) ===
echo.

REM Step 1: Login to get token
echo Step 1: Login to get JWT token...
set /p USERNAME="Username: "
set /p PASSWORD="Password: "

curl -s -X POST "http://localhost:8000/api/v1/auth/login/" ^
  -H "Content-Type: application/json" ^
  -d "{\"username\": \"%USERNAME%\", \"password\": \"%PASSWORD%\"}" ^
  > login_response.json

echo Login response saved to login_response.json
echo Please copy the "access" token from the file and paste it below:
set /p ACCESS_TOKEN="Access Token: "

echo.
echo === Testing Voice Upload ===
echo.

REM Step 2: Test upload with token
echo Step 2: Test voice upload WITH token...

REM Create test audio file if it doesn't exist
if not exist test_audio.webm (
  echo Creating test audio file...
  echo. > test_audio.webm
)

curl -X POST "http://localhost:8000/api/v1/voice/upload/" ^
  -H "Authorization: Bearer %ACCESS_TOKEN%" ^
  -F "audio_file=@test_audio.webm" ^
  -F "live_transcript=update question 3 as 8 marks" ^
  -F "context_class=1" ^
  -F "context_section=B" ^
  -F "context_roll_number=14" ^
  -F "context_subject_id=1"

echo.
echo.

REM Step 3: Test upload without token (should fail)
echo Step 3: Test voice upload WITHOUT token (should fail with 401)...
curl -X POST "http://localhost:8000/api/v1/voice/upload/" ^
  -F "audio_file=@test_audio.webm"

echo.
echo.

REM Step 4: Test upload without file (should fail)
echo Step 4: Test voice upload WITHOUT file (should fail with 400)...
curl -X POST "http://localhost:8000/api/v1/voice/upload/" ^
  -H "Authorization: Bearer %ACCESS_TOKEN%" ^
  -F "live_transcript=test"

echo.
echo.

echo === Test Complete ===
echo Check the responses above:
echo - Step 2 should show HTTP 200 with command_id, intent, etc.
echo - Step 3 should show HTTP 401 (Unauthorized)
echo - Step 4 should show HTTP 400 (Bad Request - missing audio_file)

pause
