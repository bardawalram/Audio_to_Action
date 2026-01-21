# Voice Command Format Guide - Question-Wise Marks

## ✅ CRITICAL FIX Applied

**Bug Found:** The views.py was using RAW transcription instead of NORMALIZED text for intent and entity extraction.

**Fixed:**
- Line 127: `IntentExtractor.extract_intent(normalized_text)` ✓
- Line 165: `EntityExtractor.extract_entities(normalized_text, ...)` ✓
- Added fix for "oceans" → "questions" mishearing

## 📝 Proper Command Format

### For Batch Updates (Multiple Questions)

**REQUIRED:**you MUST say the "AS" keyword between questions and marks.

**Correct Examples:**
```
"Questions 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 AS 7, 8, 9, 1, 2, 3, 4, 5, 6, 8"
"Questions 1 2 3 4 5 AS 6 7 8 9 10"
"Question 1 and 2 and 3 AS 5 and 6 and 7"
```

**Wrong Examples (Will NOT work):**
```
❌ "Questions 1, 2, 3 67, 89" - Missing "AS"
❌ "Questions 123. 456." - Missing "AS"
❌ "Questions 1, 2, 3 until 200" - No marks specified
```

### How the Normalization Works

**When you say (fast):** "1,2,3,4,5,6,7,8,9,10 as 7,8,9,1,2,3,4,5,6,8"

**Whisper transcribes:** "questions 12345678910 as 7891234568"

**Normalization converts to:** "questions 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 as 7, 8, 9, 1, 2, 3, 4, 5, 6, 8"

**Result:** 10 question-marks pairs correctly extracted ✓

### For Single Question Updates

**Format:** "Update question [NUMBER] to [MARKS] marks"

**Examples:**
```
"Update question 3 to 8 marks"
"Question 1 as 7"
"Set question 5 to 10"
```

## 🧪 Test the Fix

Try saying this command:
```
"Questions 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 AS 7, 8, 9, 1, 2, 3, 4, 5, 6, 8"
```

### Expected Backend Logs:
```
=== VOICE COMMAND PROCESSING ===
Transcription text: 'questions 12345678910 as 7891234568'
Normalized text: 'questions 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 as 7, 8, 9, 1, 2, 3, 4, 5, 6, 8'
Detected intent: BATCH_UPDATE_QUESTION_MARKS
```

### Expected Frontend Result:
- No errors ✓
- Confirmation dialog shows 10 question-marks pairs ✓
- Clean error messages (no object rendering) ✓

## 🔍 Troubleshooting

### Issue: "Unknown intent" Error

**Cause:** Missing "AS" keyword or unrecognized command format

**Solution:** Make sure to say "AS" between questions and marks:
- ✓ "Questions 1, 2, 3 AS 4, 5, 6"
- ✗ "Questions 1, 2, 3 marks 4, 5, 6"

### Issue: "Oceans" instead of "Questions"

**Fixed:** Normalization now converts "oceans" → "questions"

### Issue: Numbers not splitting correctly

**Cause:** Normalization works, but only for numbers immediately after "questions" and after "as"

**Solution:** Speak clearly with "AS" keyword:
- The numbers BEFORE "as" are treated as questions
- The numbers AFTER "as" are treated as marks

## 📊 What's Fixed

1. ✅ **Critical Bug:** views.py now uses normalized text for intent/entity extraction
2. ✅ **Error Handling:** voiceService.js extracts clean error messages
3. ✅ **React Crash:** Notification.jsx safely handles objects
4. ✅ **Normalization:** Smart splitting of merged numbers (12345678910 → 1,2,3,4,5,6,7,8,9,10)
5. ✅ **Mishearing:** "Oceans" → "Questions" conversion added

## 🎯 Success Criteria

- Say: "Questions 1 to 10 AS 7, 8, 9, 1, 2, 3, 4, 5, 6, 8"
- Backend logs show normalized text ✓
- Intent: BATCH_UPDATE_QUESTION_MARKS ✓
- 10 question-marks pairs extracted ✓
- Confirmation dialog shows all 10 updates ✓
- No React crashes ✓
