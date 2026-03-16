# Quick Test Guide - All Fixes Applied

## ✅ SERVERS RUNNING
- **Backend:** http://127.0.0.1:8000 (Auto-reloaded with all fixes)
- **Frontend:** http://localhost:5173

---

## 🧪 TEST THESE COMMANDS

### Test 1: Decimal in Command (Range Expansion Bug Fix)
**Say:** `"Change question 5 to 7.5 marks"`

**Before Fix:**
- Whisper: `"Change question 5:00 to. 7.5 marks."`
- Normalized (WRONG): `"change question 5, 6, 7.5 marks"` (expanded "to 7")
- Intent: BATCH → Failed

**After Fix:**
- Whisper: `"Change question 5:00 to. 7.5 marks."`
- Normalized: `"change question 5 7.5 marks"` (NOT expanded)
- Intent: UPDATE_QUESTION_MARKS ✓
- Dialog: Shows single question update ✓

---

### Test 2: CLARIFY Intent (No More 400 Errors)
**Say:** `"Question one two three"` (incomplete command)

**Before Fix:**
- Intent: UNKNOWN
- HTTP: 400 Bad Request ❌
- Frontend: Error toast, crashes

**After Fix:**
- Intent: CLARIFY
- HTTP: 200 OK ✓
- Frontend: Yellow dialog with examples ✓
- Button: "OK" (no Confirm button)

---

### Test 3: Flexible Single Question
**Say:** `"Update question 3 8"` (no "to")

**Before Fix:**
- Intent: UNKNOWN (required "to" keyword)

**After Fix:**
- Intent: UPDATE_QUESTION_MARKS ✓
- Pattern: `r'(?:change|update|set)\s+question\s+(\d+)\s+(\d+(?:\.\d+)?)'`
- Dialog: Shows Q3 = 8 marks ✓

---

### Test 4: Batch Update (Should Still Work)
**Say:** `"Questions 1, 2, 3 AS 4, 5, 6"`

**Whisper transcribes:** `"Questions 123 as 456"`

**Normalization:**
- Smart split: `"questions 1, 2, 3 as 4, 5, 6"` ✓

**Result:**
- Intent: BATCH_UPDATE_QUESTION_MARKS ✓
- Dialog: Shows 3 updates ✓

---

### Test 5: Range Expansion
**Say:** `"Questions 1 to 5 AS 6, 7, 8, 9, 10"`

**Normalization:**
- Range expand: `"questions 1, 2, 3, 4, 5 as 6, 7, 8, 9, 10"` ✓

**Result:**
- Intent: BATCH_UPDATE_QUESTION_MARKS ✓
- Dialog: Shows 5 updates ✓

---

## 📊 HOW TO VERIFY

### Backend Console (MUST SHOW):
```
=== VOICE COMMAND PROCESSING ===
Transcription text: '<what you said>'
Normalized text: '<after all fixes>'
Detected intent: <BATCH_UPDATE_QUESTION_MARKS | UPDATE_QUESTION_MARKS | CLARIFY>
```

### Frontend Browser Console (F12):
```javascript
[FloatingVoiceButton] Upload result: {...}
[FloatingVoiceButton] Intent: "CLARIFY"  // or other intent
[ConfirmationDialog] Rendering with:
```

### UI Behavior:
- **Valid commands:** Blue confirmation dialog with data table
- **Invalid commands:** Yellow CLARIFY dialog with examples
- **No red error toasts**
- **No "Unknown intent" messages**
- **No 400 errors in network tab**

---

## 🔍 IF SOMETHING FAILS

1. **Check Backend Console First:**
   - What is the "Normalized text"?
   - What is the "Detected intent"?

2. **If Intent = UNKNOWN but should be valid:**
   - Pattern mismatch → Need to add pattern
   - Share the normalized text

3. **If Intent = BATCH but should be SINGLE:**
   - Check normalized text - does it have 3+ question numbers?
   - May need stricter batch pattern

4. **If Still Getting 400 Error:**
   - Check if Django reloaded (should show timestamp in logs)
   - Restart Django if needed: `python manage.py runserver`

---

## ✅ SUCCESS CRITERIA

- ✅ "Change question 5 to 7.5" → Single update dialog
- ✅ "Question one two three" → Yellow CLARIFY dialog
- ✅ "Update question 3 8" → Single update (no "to" needed)
- ✅ "Questions 1, 2, 3 AS 4, 5, 6" → Batch update
- ✅ No 400 errors anywhere
- ✅ All responses return 200 OK

---

## 🎯 CURRENT STATUS

**All fixes applied and servers running:**
- STT normalization: ✓
- Flexible patterns: ✓
- CLARIFY intent system: ✓
- Frontend CLARIFY dialog: ✓
- Range expansion bug fix: ✓
- Status enum fix: ✓

**Ready for testing!**

Test now and report any failures with:
1. Command you said
2. Backend console output
3. Browser console output (F12)
