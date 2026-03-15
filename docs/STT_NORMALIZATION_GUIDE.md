# STT Normalization & Batch Parsing Guide

## 🎯 Problem Statement

Whisper STT converts spoken homophones into numbers:
- **"to"/"too"** → `2`
- **"for"** → `4`
- **"one"** → `1` (sometimes)

This breaks NLP parsing because the system expects keywords, not numeric tokens.

### Example Problem
```
Spoken:  "Update marks for questions 1, 2, 3 as 4, 5, 6"
Whisper: "update marks 4 questions 1 2 3 as 4 5 6"
         ↑              ↑
         Missing "for"  Missing commas
```

---

## ✅ Solution Implemented

### 1. Text Normalization Layer

**File**: `backend/apps/voice_processing/intent_extractor.py`

**Function**: `IntentExtractor.normalize_stt_text(text)`

**What it does**:
1. Converts `"4"` → `"for"` when used as preposition
2. Inserts commas between number sequences
3. Preserves actual numeric values for questions/marks

**Example Transform**:
```python
Input:  "update marks 4 questions 1 2 3 as 4 5 6"
Output: "update marks for questions 1, 2, 3 as 4, 5, 6"
```

### Normalization Rules

```python
# Rule 1: "update marks 4 questions" → "update marks for questions"
text = re.sub(
    r'\b(update|change|set|enter)\s+marks?\s+4\s+(questions?|roll|rule)',
    r'\1 marks for \2',
    text
)

# Rule 2: "questions 1 2 3" → "questions 1, 2, 3"
text = re.sub(
    r'question[s]?\s+(\d+)\s+(\d+)\s+(\d+)',
    r'questions \1, \2, \3',
    text
)

# Rule 3: "as 4 5 6" → "as 4, 5, 6"
text = re.sub(
    r'as\s+(\d+)\s+(\d+)\s+(\d+)',
    r'as \1, \2, \3',
    text
)

# Rule 4: Aggressive comma insertion after keywords
text = re.sub(
    r'(questions?|marks?|as|give)\s+(\d+)(\s+\d+)+',
    lambda m: m.group(1) + ' ' + ', '.join(m.group(0).split()[1:]),
    text
)
```

---

### 2. Parallel List Parser

**What it does**: Parses commands where questions and marks are listed separately, then zips them together.

**Pattern**: `questions 1, 2, 3 as 4, 5, 6`

**Extraction Logic**:
```python
# Pattern to detect parallel lists
parallel_pattern = r'questions?\s+([\d,\s]+)\s+(?:as|marks?|give)\s+([\d,\s]+)'

if match:
    # Extract numbers from each side
    question_nums = [int(x) for x in re.findall(r'\d+', left_side)]
    marks_nums = [float(x) for x in re.findall(r'\d+(?:\.\d+)?', right_side)]

    # Validate lengths match
    if len(question_nums) == len(marks_nums):
        # Zip them together
        for q_num, mark in zip(question_nums, marks_nums):
            updates.append({
                'question_number': q_num,
                'marks_obtained': mark
            })
```

**Result**:
```json
{
  "intent": "BATCH_UPDATE_QUESTION_MARKS",
  "updates": [
    { "question_number": 1, "marks_obtained": 4.0 },
    { "question_number": 2, "marks_obtained": 5.0 },
    { "question_number": 3, "marks_obtained": 6.0 }
  ]
}
```

---

### 3. Fallback: Pair-wise Parser

If parallel list parsing fails, falls back to traditional pair-wise extraction:

**Patterns**:
```python
# Pattern 1: "1 marks 3"
r'(?:question\s+)?(\d+)\s+(?:marks?|is|give)\s+(\d+(?:\.\d+)?)'

# Pattern 2: "for 1 give 3"
r'(?:for\s+)?(?:question\s+)?(\d+)\s+give\s+(\d+(?:\.\d+)?)'

# Pattern 3: "question 1 is 3"
r'question\s+(\d+)\s+is\s+(\d+(?:\.\d+)?)'

# Pattern 4: "1 -> 3" or "1: 3"
r'(\d+)\s*(?:->|:|to)\s*(\d+(?:\.\d+)?)'
```

---

## 🧪 Test Cases

### Test Case 1: Basic Parallel List
```
Input (Spoken):  "Update marks for questions 1, 2, 3 as 4, 5, 6"
Input (Whisper): "update marks 4 questions 1 2 3 as 4 5 6"
Normalized:      "update marks for questions 1, 2, 3 as 4, 5, 6"
Intent:          BATCH_UPDATE_QUESTION_MARKS
Updates:         Q1→4, Q2→5, Q3→6 ✅
```

### Test Case 2: Traditional Format
```
Input:      "1 marks 3, 2 marks 5, 3 marks 7"
Intent:     BATCH_UPDATE_QUESTION_MARKS
Updates:    Q1→3, Q2→5, Q3→7 ✅
```

### Test Case 3: "For Give" Format
```
Input:      "for 1 give 3, for 4 give 6, for 7 give 8"
Intent:     BATCH_UPDATE_QUESTION_MARKS
Updates:    Q1→3, Q4→6, Q7→8 ✅
```

### Test Case 4: "Is" Format
```
Input:      "question 1 is 3, question 2 is 5"
Intent:     BATCH_UPDATE_QUESTION_MARKS
Updates:    Q1→3, Q2→5 ✅
```

### Test Case 5: Decimal Marks
```
Input:      "questions 1, 2, 3 as 4.5, 5.5, 6.5"
Intent:     BATCH_UPDATE_QUESTION_MARKS
Updates:    Q1→4.5, Q2→5.5, Q3→6.5 ✅
```

### Test Case 6: Length Mismatch (Edge Case)
```
Input:      "questions 1, 2, 3 as 4, 5"  (3 questions, 2 marks)
Behavior:   Logs warning, falls back to pair-wise parser
Result:     May extract partial updates or fail gracefully
```

---

## 📊 Flow Diagram

```
User Voice Input
    ↓
Whisper STT
    ↓ (may convert "for" → 4, "to" → 2)
Raw Transcript: "update marks 4 questions 1 2 3 as 4 5 6"
    ↓
❶ normalize_stt_text()
    ↓
Normalized: "update marks for questions 1, 2, 3 as 4, 5, 6"
    ↓
❷ extract_intent()
    ↓
Intent: BATCH_UPDATE_QUESTION_MARKS
    ↓
❸ extract_entities()
    ├─ Try parallel_pattern first
    │   └─> "questions 1, 2, 3 as 4, 5, 6"
    │        ├─ Extract left: [1, 2, 3]
    │        ├─ Extract right: [4, 5, 6]
    │        └─ Zip: [(1,4), (2,5), (3,6)] ✅
    │
    └─ If parallel fails, fallback to pair-wise patterns
    ↓
Entities: {
  "updates": [
    {"question_number": 1, "marks_obtained": 4.0},
    {"question_number": 2, "marks_obtained": 5.0},
    {"question_number": 3, "marks_obtained": 6.0}
  ]
}
    ↓
Backend Execution (Batch Update)
    ↓
Frontend Confirmation Dialog (Table Preview)
    ↓
User Confirms
    ↓
All 3 questions updated in 1 transaction ✅
Grand total recalculated ✅
localStorage synced ✅
Marksheet updates instantly ✅
```

---

## 🔧 Running Unit Tests

```bash
cd backend
pytest apps/voice_processing/tests/test_stt_normalization.py -v
```

**Expected Output**:
```
test_for_to_4_conversion PASSED
test_comma_insertion_after_questions PASSED
test_parallel_list_basic PASSED
test_parallel_list_with_stt_quirk PASSED
test_traditional_format PASSED
test_real_world_example1 PASSED
```

---

## 🎤 Voice Commands to Test

### Test in QuestionWisePage (with context):

1. **Parallel List**:
   - Say: "Update marks for questions 1, 2, 3 as 4, 5, 6"
   - Expected: 3 updates

2. **Natural Speech** (will become "4" in transcript):
   - Say: "Update marks for questions 1, 2, 3 as 4, 5, 6"
   - Whisper: "update marks 4 questions 1 2 3 as 4 5 6"
   - Expected: Still works ✅

3. **Traditional Format**:
   - Say: "1 marks 3, 2 marks 5, 3 marks 7"
   - Expected: 3 updates

4. **For-Give Format**:
   - Say: "For 1 give 3, for 4 give 6"
   - Expected: 2 updates

---

## 🚀 Success Criteria

- ✅ Saying "to/too/for" does NOT break parsing
- ✅ Parallel lists work: "questions 1, 2, 3 as 4, 5, 6"
- ✅ Traditional formats still work: "1 marks 3, 2 marks 5"
- ✅ Decimal marks supported: "4.5"
- ✅ All updates applied in 1 batch
- ✅ Grand total recalculates correctly
- ✅ Marksheet updates without page refresh

---

## 🐛 Debugging

If a command isn't working:

1. **Check Backend Logs**:
   ```
   Normalizing STT text: 'update marks 4 questions 1 2 3 as 4 5 6'
   Normalized text: 'update marks for questions 1, 2, 3 as 4, 5, 6'
   Intent detected: BATCH_UPDATE_QUESTION_MARKS
   Detected PARALLEL LIST pattern
   Questions: [1, 2, 3]
   Marks: [4, 5, 6]
   Parallel list parsing: 3 updates created
   ```

2. **Check Intent Detection**:
   - If intent is `UNKNOWN`, the normalization may have failed
   - Check if the batch pattern is being triggered

3. **Check Entity Extraction**:
   - Should see "Detected PARALLEL LIST pattern" in logs
   - If it falls back to pair-wise, check why parallel didn't match

4. **Validate Context**:
   - Ensure `roll_number`, `subject_id`, `class`, `section` are passed from QuestionWisePage

---

## 📝 Key Files Modified

1. **Backend**:
   - `backend/apps/voice_processing/intent_extractor.py`
     - Added `normalize_stt_text()` method
     - Enhanced `_extract_batch_question_marks_entities()` with parallel list parsing

2. **Frontend** (already done in previous steps):
   - `frontend/src/components/marks/BatchQuestionMarksPreview.jsx`
   - `frontend/src/components/voice/ConfirmationDialog.jsx`

3. **Tests**:
   - `backend/apps/voice_processing/tests/test_stt_normalization.py`

---

## 💡 Future Enhancements

1. **AI-based normalization**: Use a small LLM to intelligently convert numbers to words
2. **Context-aware disambiguation**: Detect if "4" is a number or "for" based on grammar
3. **Support more homophones**: "ate" → 8, "won" → 1, etc.
4. **Multi-language support**: Handle Hindi/regional language homophones

---

**Last Updated**: 2026-01-20
**Status**: ✅ Fully Implemented & Tested
