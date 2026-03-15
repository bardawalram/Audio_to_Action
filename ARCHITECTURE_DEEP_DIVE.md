# Audio_to_Action — Complete Architecture Deep Dive

> Voice-Driven School ERP System (ReATOA)
> Last Updated: February 2026

---

## Table of Contents

1. [Current Tech Stack](#1-current-tech-stack)
2. [Complete End-to-End Workflow](#2-complete-end-to-end-workflow)
   - [Phase 1: Audio Capture](#phase-1-audio-capture-frontend)
   - [Phase 2: Upload to Backend](#phase-2-upload-to-backend)
   - [Phase 3: Backend Processing Pipeline](#phase-3-backend-processing-pipeline-6-stages)
   - [Phase 4: Confirmation Dialog](#phase-4-confirmation-dialog-frontend)
   - [Phase 5: Execution](#phase-5-execution-backend)
   - [Phase 6: UI Update](#phase-6-ui-update-frontend)
3. [Database Schema](#3-database-schema)
4. [STT Normalization Pipeline](#4-stt-normalization-pipeline)
5. [Intent Detection System](#5-intent-detection-system)
6. [Entity Extraction](#6-entity-extraction)
7. [Edge Cases Handled](#7-edge-cases-handled-20)
8. [Key Design Decisions](#8-key-design-decisions)
9. [Limitations of Current System](#9-limitations-of-current-system)
10. [Scaling for Complex ERP — What to Change](#10-scaling-for-complex-erp--what-to-change)
11. [Recommended Tech Stack for Complex ERP](#11-recommended-tech-stack-for-complex-erp)
12. [Proposed Architecture Diagram](#12-proposed-architecture-diagram)
13. [Cost Comparison](#13-cost-comparison)
14. [Migration Priority](#14-migration-priority)
15. [File Reference](#15-file-reference)

---

## 1. Current Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend Framework** | React 18.2 + Vite 5.0 | SPA with fast HMR |
| **State Management** | Redux Toolkit 2.0 | Global state (auth, voice, ui, fee) |
| **Styling** | Tailwind CSS 3.4 | Utility-first CSS |
| **Audio Recording** | MediaRecorder API (Browser) | Captures audio as WebM blob |
| **Live Transcription** | Web Speech API (Browser) | Real-time interim transcript |
| **HTTP Client** | Axios 1.6 | API calls with JWT interceptors |
| **Backend Framework** | Django 5.0 + DRF | REST API |
| **Speech-to-Text** | OpenAI Whisper (local model) | Offline audio transcription |
| **NLP / Intent Engine** | Custom Regex + Keyword matching | 4,000+ lines of hand-coded rules |
| **Database** | PostgreSQL 15 / SQLite (dev) | Relational storage |
| **Authentication** | JWT (SimpleJWT) | Access + Refresh tokens |
| **Containerization** | Docker Compose | PostgreSQL service |
| **Icons** | Heroicons 2.1 | UI icons |
| **Routing** | React Router 6.21 | Frontend routing |

---

## 2. Complete End-to-End Workflow

### Phase 1: Audio Capture (Frontend)

```
User clicks FloatingVoiceButton (bottom-right corner, visible on all pages)
         |
         v
+-----------------------------------------------+
|  TWO PARALLEL SYSTEMS START SIMULTANEOUSLY     |
|                                                |
|  1. MediaRecorder API                          |
|     - Captures raw audio as WebM blob          |
|     - Stores chunks in memory                  |
|     - File: src/hooks/useVoiceRecorder.js      |
|                                                |
|  2. Web Speech API (webkitSpeechRecognition)   |
|     - Real-time transcript (interim + final)   |
|     - Shows live text as user speaks           |
|     - Language: en-US, continuous mode          |
|     - File: src/hooks/useSpeechRecognition.js  |
+-----------------------------------------------+
         |
   User clicks STOP
         |
         v
   Wait 500ms for transcript finalization
         |
         v
   Collect: audioBlob + liveTranscript + pageContext
```

**Context captured from current page URL:**

| Context Field | Example | Source |
|--------------|---------|--------|
| `context_class` | `8` | URL param `:classNum` |
| `context_section` | `B` | URL param `:section` |
| `context_roll_number` | `5` | URL param `:rollNumber` |
| `context_subject_id` | `3` | URL param `:subjectId` |
| `context_page` | `/marks/8/B` | `useLocation().pathname` |

### Phase 2: Upload to Backend

```http
POST /api/v1/voice/upload/
Content-Type: multipart/form-data

FormData:
  audio_file:          <WebM blob>
  live_transcript:     "update marks for roll 5 maths 95 hindi 88"
  context_class:       "8"
  context_section:     "B"
  context_page:        "/marks/8/B"
```

**Frontend code flow:**
1. `FloatingVoiceButton.handleUpload()` triggers
2. Calls `voiceService.uploadVoiceCommand(audioBlob, context, liveTranscript)`
3. Dispatches `uploadStart()` to Redux voice slice
4. On success: dispatches `uploadSuccess()` with `{command_id, intent, confirmationData}`

### Phase 3: Backend Processing Pipeline (6 Stages)

#### Stage 1: File Validation

```python
# File: backend/apps/voice_processing/views.py
# Serializer: VoiceCommandUploadSerializer

MAX_AUDIO_FILE_SIZE = 10MB
ALLOWED_FORMATS = ['audio/webm', 'audio/wav', 'audio/mp3', 'audio/m4a', 'audio/flac']

# Creates database record
voice_command = VoiceCommand.objects.create(
    user=request.user,
    audio_file=audio_file,           # Saved to /media/voice_commands/YYYY/MM/DD/
    status='PENDING_CONFIRMATION'
)
```

#### Stage 2: Speech-to-Text

```python
# File: backend/apps/voice_processing/speech_to_text.py
# Class: WhisperTranscriber

# Option A (preferred): Use live transcript from Web Speech API
if live_transcript and live_transcript.strip():
    voice_command.transcription = live_transcript.strip()

# Option B (fallback): Run Whisper model locally
model = WhisperTranscriber.get_model()   # Lazy-loads, cached after first call
result = model.transcribe(
    audio_file_path,
    language='en',
    fp16=False  # True if GPU available
)
voice_command.transcription = result['text'].strip()

# Model size configurable: WHISPER_MODEL_SIZE = 'base' | 'small' | 'medium' | 'large'
# Device configurable: WHISPER_DEVICE = 'cpu' | 'cuda'
```

#### Stage 3: Text Normalization (8-Step Pipeline)

> See [Section 4](#4-stt-normalization-pipeline) for full details.

```
Input:  "questions 12345678910 as 56789234"
Output: "questions 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 as 5, 6, 7, 8, 9, 2, 3, 4"
```

#### Stage 4: Intent Detection

> See [Section 5](#5-intent-detection-system) for full details.

```python
# File: backend/apps/voice_processing/intent_extractor.py
# Method: IntentExtractor.extract_intent()

# Strategy 1: Regex pattern matching (25+ patterns per intent)
# Strategy 2: Keyword fallback (for noisy environments)
# Returns one of 24+ intents

# + Role-based filtering:
TEACHER_INTENTS = {UPDATE_MARKS, ENTER_MARKS, MARK_ATTENDANCE, ...}
ACCOUNTANT_INTENTS = {COLLECT_FEE, SHOW_FEE_DETAILS, SHOW_DEFAULTERS, ...}
```

#### Stage 5: Entity Extraction

> See [Section 6](#6-entity-extraction) for full details.

```python
# Extracts structured data per intent type
# Falls back to page context if class/section missing from voice
```

#### Stage 6: Completeness Check + Confirmation Prep

```python
# File: backend/apps/voice_processing/intent_extractor.py
# Method: check_command_completeness()

# Check for trailing prepositions (incomplete command)
if text.endswith(('for', 'to', 'of', 'in', 'with', 'as', 'and')):
    return is_complete=False, missing=['value after preposition']

# Intent-specific requirements:
# UPDATE_MARKS     -> needs roll_number + subject_marks
# COLLECT_FEE      -> needs amount + roll_number
# OPEN_MARKS_SHEET -> needs class_number + section

# CRITICAL DESIGN: NEVER returns HTTP 400. Always 200 OK.
# Unknown -> returns intent="CLARIFY" with helpful examples
```

**Response to frontend:**
```json
{
  "command_id": 42,
  "transcription": "update marks for roll 5 maths 95 hindi 88",
  "intent": "UPDATE_MARKS",
  "confirmation_data": {
    "student": {"id": 5, "name": "John Doe", "roll_number": 5, "class": "8B"},
    "exam_type": {"id": 1, "name": "Unit Test"},
    "marks_table": [
      {"subject": "Mathematics", "subject_code": "MATH", "marks_obtained": 95, "max_marks": 100},
      {"subject": "Hindi", "subject_code": "HINDI", "marks_obtained": 88, "max_marks": 100}
    ]
  },
  "needs_confirmation": true
}
```

### Phase 4: Confirmation Dialog (Frontend)

```
File: src/components/voice/ConfirmationDialog.jsx (1200+ lines)

Renders DIFFERENT preview component per intent:

+----------------------------+----------------------------+
| Intent                     | Preview Component          |
+----------------------------+----------------------------+
| UPDATE_MARKS               | MarksPreview               |
| ENTER_MARKS                | MarksPreview               |
| UPDATE_QUESTION_MARKS      | QuestionMarksPreview       |
| BATCH_UPDATE_QUESTION_MARKS| BatchQuestionMarksPreview  |
| MARK_ATTENDANCE            | AttendancePreview          |
| COLLECT_FEE                | FeeCollectionPreview       |
| SHOW_FEE_DETAILS           | FeeDetailsPreview          |
| SHOW_DEFAULTERS            | DefaultersPreview          |
| TODAY_COLLECTION           | TodayCollectionPreview     |
| VIEW_STUDENT               | StudentDetailsPreview      |
| DOWNLOAD_PROGRESS_REPORT   | ProgressReportPreview      |
| Navigation intents         | NavigationPreview          |
| CLARIFY                    | Yellow alert + examples    |
| INCOMPLETE                 | Orange alert + missing     |
| BATCH_INCOMPLETE           | Form with editable inputs  |
| SELECT_SECTION             | Grid of section buttons    |
| SELECT_STUDENT             | Clickable student buttons  |
| DATA_NOT_FOUND             | Amber alert + suggestions  |
| CANCEL                     | Auto-closes dialog         |
+----------------------------+----------------------------+

User can:
  - EDIT values inline before confirming
  - CONFIRM via button click or voice ("yes", "haan", "theek hai")
  - CANCEL via button click or voice ("no", "nahi", "ruko")
```

### Phase 5: Execution (Backend)

```http
POST /api/v1/voice/commands/{id}/confirm/
Body: { "edited_data": {...} }   // optional user edits
```

```python
# File: backend/apps/voice_processing/command_executor.py

@transaction.atomic   # ALL OR NOTHING
def execute(intent, entities, confirmation_data, user):

    if intent == 'UPDATE_MARKS':
        for mark_data in confirmation_data['marks_table']:
            Marks.objects.update_or_create(
                student=student,
                subject=subject,
                exam_type=exam_type,
                defaults={'marks_obtained': mark_data['marks_obtained']}
            )
            AuditLog.objects.create(...)   # Every change logged

    elif intent == 'MARK_ATTENDANCE':
        session, _ = AttendanceSession.objects.get_or_create(
            class_section=class_section, date=today
        )
        for student in students:
            AttendanceRecord.objects.update_or_create(
                session=session, student=student,
                defaults={'status': 'PRESENT'}
            )

    elif intent == 'COLLECT_FEE':
        FeeTransaction.objects.create(
            student=student, amount=amount,
            payment_method=method, paid_by=user
        )

    voice_command.status = 'EXECUTED'
    voice_command.save()
```

### Phase 6: UI Update (Frontend)

```
On confirm success:
    |
    +---> Update localStorage (marks cache)
    |     Key: marks_{classNum}{section}_{examType}
    |
    +---> Dispatch StorageEvent (other components listen)
    |
    +---> Dispatch custom events:
    |       - 'attendanceUpdated'  (AttendanceSheetPage listens)
    |       - 'feeCollected'       (FeeListPage listens)
    |       - 'voiceReceiptReady'  (VoiceReceiptModal listens)
    |
    +---> Show success notification (green toast, auto-hide 5s)
    |
    +---> Navigate if needed (for navigation intents)
    |
    +---> Close confirmation dialog
```

---

## 3. Database Schema

```
CustomUser (role: ADMIN | TEACHER | STUDENT | ACCOUNTANT)
    |
    +-- Teacher (employee_id, subjects[], assigned_classes[])
    |
    +-- VoiceCommand
    |   +-- audio_file       (FileField -> /media/voice_commands/YYYY/MM/DD/)
    |   +-- transcription    (TextField - result from Whisper/Web Speech)
    |   +-- intent           (CharField - detected intent type)
    |   +-- entities         (JSONField - extracted parameters)
    |   +-- confirmation_data(JSONField - pre-execution display data)
    |   +-- status           (PENDING_CONFIRMATION | CONFIRMED | REJECTED | EXECUTED | FAILED)
    |   +-- error_message    (TextField - populated on failure)
    |   +-- created_at       (DateTimeField)
    |   +-- updated_at       (DateTimeField)
    |
    +-- Class (grade_number: 1-10, name: "Class 1")
    |   +-- Section (name: "A" | "B" | "C")
    |       +-- ClassSection (class + section + academic_year)
    |
    +-- Student
    |   +-- first_name, last_name
    |   +-- roll_number
    |   +-- class_section -> ClassSection
    |   +-- date_of_birth, gender
    |   +-- is_active
    |
    +-- Subject (name, code: MATH | HINDI | ENGLISH | SCIENCE | SOCIAL | COMPUTER)
    |
    +-- ExamType (name: UNIT_TEST | MIDTERM | FINAL)
    |
    +-- Marks (unique_together: student + subject + exam_type)
    |   +-- student         -> Student
    |   +-- subject         -> Subject
    |   +-- exam_type       -> ExamType
    |   +-- marks_obtained  (DecimalField 0.00 - 100.00)
    |   +-- max_marks       (IntegerField, usually 100)
    |   +-- entered_by      -> CustomUser
    |   |
    |   +-- QuestionWiseMarks (unique_together: marks + question_number)
    |       +-- marks           -> Marks
    |       +-- question_number (IntegerField 1-50)
    |       +-- max_marks       (DecimalField)
    |       +-- marks_obtained  (DecimalField)
    |
    +-- AttendanceSession (unique_together: class_section + date)
    |   +-- class_section -> ClassSection
    |   +-- date          (DateField)
    |   +-- marked_by     -> CustomUser
    |   |
    |   +-- AttendanceRecord (unique_together: session + student)
    |       +-- session  -> AttendanceSession
    |       +-- student  -> Student
    |       +-- status   (PRESENT | ABSENT | LATE | EXCUSED)
    |
    +-- FeeTransaction
    |   +-- student        -> Student
    |   +-- amount         (DecimalField)
    |   +-- payment_method (CASH | CHEQUE | ONLINE | CARD)
    |   +-- paid_by        -> CustomUser
    |   +-- date           (DateField)
    |
    +-- AuditLog
        +-- user           -> CustomUser
        +-- action         (CREATE | UPDATE | DELETE)
        +-- model_name     (CharField)
        +-- object_id      (CharField)
        +-- old_values     (JSONField)
        +-- new_values     (JSONField)
        +-- description    (TextField)
        +-- created_at     (DateTimeField)
```

---

## 4. STT Normalization Pipeline

**File:** `backend/apps/voice_processing/intent_extractor.py` (Lines 1348-1902)

The system applies 8 sequential normalization steps to handle Whisper's transcription errors:

```
[NORM-0] Original Whisper Output
    |
[NORM-1a] Convert slashes to commas
           "10/11/12" -> "10, 11, 12"
    |
[NORM-1b] Convert periods to commas
           "7. 19." -> "7, 19"
    |
[NORM-2] Remove remaining trailing periods
           "question 3." -> "question 3"
    |
[NORM-3] Convert word numbers + fix mishearings
           "one" -> "1", "ate" -> "8", "mass" -> "maths"
           Hindi: "ek" -> "1", "do" -> "2", "teen" -> "3"
    |
[NORM-4] Smart split question numbers
           "12345678910" -> "1,2,3,4,5,6,7,8,9,10"
           Preserves 10, 11, 12 as intact multi-digit numbers
    |
[NORM-5] Smart split marks values
           "911" -> "9, 1, 1" (individual digit marks)
           "10" -> "10" (preserved as valid score)
    |
[NORM-6] Expand ranges (with decimal protection)
           "questions 1 to 10" -> "1,2,3,4,5,6,7,8,9,10"
           "5 to 7.5" -> NOT expanded (decimal detected)
    |
[NORM-7] Context-aware homophone correction
           "4" -> "for" when used as preposition
    |
[NORM-8] Add missing commas between bare numbers
           "questions 1 2 3" -> "questions 1, 2, 3"
    |
    v
Final Normalized Text
```

### Normalization Details

#### Homophones & Sound Confusions

```python
# Number homophones
'won' -> '1',  'too' -> '2',  'tree' -> '3'
'ate' -> '8',  'free' -> 'fee' (context-sensitive)
'rule' -> 'roll',  'marx' -> 'marks'
```

#### Subject Name Mishearings

```python
'mass' -> 'maths',  'match' -> 'maths',  'moths' -> 'maths',  'mats' -> 'maths'
'indy' -> 'hindi',  'indie' -> 'hindi',  'hind' -> 'hindi'
'signs' -> 'science',  'silence' -> 'science'
'so shall' -> 'social'
'enlist' -> 'english'
```

#### Hindi Number Words

```python
'ek' -> '1',  'do' -> '2',  'teen' -> '3',  'chaar' -> '4',  'paanch' -> '5'
'chhe' -> '6',  'saat' -> '7',  'aath' -> '8',  'nau' -> '9',  'das' -> '10'
'bees' -> '20',  'tees' -> '30'
```

#### Whisper-Specific Mishearing Fixes

```python
'choose' -> 'to'       # Whisper commonly mishears "to"
'pin' -> 'open'        # Whisper mishearing
'date' -> 'update'     # Whisper mishearing
'5:00' -> '5'          # Removes time notation
'months' -> 'marks'    # Context-sensitive
'mugs' -> 'marks'      # Context-sensitive
```

#### Smart Number Splitting Algorithm

```python
# Question numbers: Detect consecutive sequences, preserve 10/11/12
"12345678910"    -> "1, 2, 3, 4, 5, 6, 7, 8, 9, 10"     # Preserves "10"
"1234567891011"  -> "1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11"  # Preserves "10", "11"
"123456789101112"-> "1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12"

# Marks values: Preserve valid scores (0-9, 10), split rest
"911"  -> "9, 1, 1"    # Three individual marks
"10"   -> "10"          # Valid score, preserved
"1112" -> "11, 12"      # Both valid scores
```

---

## 5. Intent Detection System

**File:** `backend/apps/voice_processing/intent_extractor.py` (Lines 1904-1934)

### All 24+ Supported Intents

| Category | Intent | Trigger Examples |
|----------|--------|-----------------|
| **Marks** | `ENTER_MARKS` | "Enter marks for roll 5 maths 95 hindi 88" |
| | `UPDATE_MARKS` | "Update marks for roll 5 science 92" |
| | `UPDATE_QUESTION_MARKS` | "Change question 5 to 7.5 marks" |
| | `BATCH_UPDATE_QUESTION_MARKS` | "Questions 1, 2, 3 AS 4, 5, 6" |
| | `OPEN_MARKS_SHEET` | "Open class 8B marks" |
| | `OPEN_QUESTION_SHEET` | "Open question wise for roll 5" |
| **Attendance** | `MARK_ATTENDANCE` | "Mark all present except roll 3, 7" |
| | `OPEN_ATTENDANCE_SHEET` | "Open attendance for class 9A" |
| **Fees** | `COLLECT_FEE` | "Collect 5000 from roll 12" |
| | `SHOW_FEE_DETAILS` | "Show fee details for roll 8" |
| | `SHOW_DEFAULTERS` | "Show fee defaulters" |
| | `TODAY_COLLECTION` | "Today's total collection" |
| | `OPEN_FEE_PAGE` | "Go to fee collection" |
| **Navigation** | `NAVIGATE_MARKS` | "Go to marks" |
| | `NAVIGATE_ATTENDANCE` | "Go to attendance" |
| | `NAVIGATE_DASHBOARD` | "Go home" |
| | `NAVIGATE_REPORTS` | "Go to reports" |
| | `NAVIGATE_FEE_REPORTS` | "Show fee analytics" |
| **Views** | `VIEW_STUDENT` | "Show details of roll 22" |
| | `DOWNLOAD_PROGRESS_REPORT` | "Download report for roll 5" |
| **System** | `SELECT_SECTION` | "Open class 1" (section needed) |
| | `SELECT_EXAM_TYPE` | "Choose midterm" |
| | `CANCEL` | "Cancel", "undo", "go back" |
| | `UNKNOWN` -> `CLARIFY` | Unrecognized command |

### Detection Strategy

```python
# Strategy 1: Regex Pattern Matching (primary, most accurate)
for intent, patterns in INTENT_PATTERNS.items():
    for pattern in patterns:                              # 25+ patterns per intent
        if re.search(pattern, normalized_text, re.IGNORECASE):
            return intent

# Strategy 2: Keyword Fallback (for noisy environments)
if no_pattern_matched:
    fallback_intent, confidence = _keyword_fallback(text)
    if confidence > threshold:
        return fallback_intent

# Default: UNKNOWN -> converted to CLARIFY with helpful examples
return 'UNKNOWN'
```

### Role-Based Intent Filtering

```python
ACCOUNTANT_INTENTS = {
    'COLLECT_FEE', 'SHOW_FEE_DETAILS', 'OPEN_FEE_PAGE',
    'SHOW_DEFAULTERS', 'TODAY_COLLECTION', 'NAVIGATE_FEE_REPORTS',
    'NAVIGATE_DASHBOARD', 'CANCEL', 'UNKNOWN'
}

TEACHER_INTENTS = {
    'UPDATE_MARKS', 'ENTER_MARKS', 'MARK_ATTENDANCE', 'VIEW_STUDENT',
    'NAVIGATE_MARKS', 'NAVIGATE_ATTENDANCE', 'NAVIGATE_REPORTS',
    'OPEN_MARKS_SHEET', 'OPEN_ATTENDANCE_SHEET', 'SELECT_EXAM_TYPE',
    'UPDATE_QUESTION_MARKS', 'BATCH_UPDATE_QUESTION_MARKS',
    'DOWNLOAD_PROGRESS_REPORT', ...
}

# If ACCOUNTANT tries marks intent -> redirected to fee page
# If role mismatch -> redirected to dashboard
```

---

## 6. Entity Extraction

**File:** `backend/apps/voice_processing/intent_extractor.py` — `EntityExtractor` class

### Entities Extracted Per Intent

**ENTER_MARKS / UPDATE_MARKS:**
```json
{
  "roll_number": 5,
  "class": 8,
  "section": "B",
  "marks": {
    "MATH": 95,
    "HINDI": 88,
    "ENGLISH": 92,
    "SCIENCE": 80,
    "SOCIAL": 85
  }
}
```

**BATCH_UPDATE_QUESTION_MARKS:**
```json
{
  "updates": [
    {"question_number": 1, "marks_obtained": 5.0},
    {"question_number": 2, "marks_obtained": 6.0},
    {"question_number": 3, "marks_obtained": 7.0}
  ],
  "roll_number": 5
}
```

**MARK_ATTENDANCE:**
```json
{
  "class": 8,
  "section": "B",
  "mark_all": true,
  "status": "PRESENT",
  "excluded_rolls": [3, 7, 15]
}
```

**COLLECT_FEE:**
```json
{
  "amount": 5000,
  "roll_number": 12,
  "class": 6,
  "section": "A",
  "payment_method": "CASH",
  "student_name": "Ram Kumar"
}
```

### Context Fallback

```python
# If class/section not extracted from voice, use page context
if 'class' not in entities and context.get('class'):
    entities['class'] = context['class']
if 'section' not in entities and context.get('section'):
    entities['section'] = context['section']
```

---

## 7. Edge Cases Handled (20+)

### 1. Homophones & Similar Sounds

| Spoken | Misheard As | Handling |
|--------|-------------|---------|
| "to" | "2" | Context-aware: "update marks **to** 90" |
| "for" | "4" | Context-aware: "marks **for** roll 1" |
| "one" | "won" | Word-to-number conversion |
| "eight" | "ate" | Word-to-number conversion |

### 2. Subject Name Mishearings

Uses fuzzy matching: "mass" / "match" / "moths" / "mats" all resolve to "MATH"

### 3. Number Confusion

- Teen vs Ty: "15" misheard as "50", "13" as "30"
- Similar: 90 vs 19, 80 vs 18
- Decimal: "7.5" vs "7, 5" vs "75"
- Validation: marks checked against range (0-100)

### 4. Mid-Sentence Corrections

```
"Update maths... no wait, science marks 90"
-> Discards "maths", uses "science"

Correction keywords: "sorry", "actually", "I mean", "I meant", "no wait"
```

### 5. Background Noise

- Human noise: students talking, other teachers
- Environmental: bell, PA system, fan/AC, traffic
- Handling: noise gate, voice activity detection

### 6. Incomplete / Interrupted Commands

```
"Update marks for roll..."  -> Detected as incomplete (trailing preposition)
"Mark attendance for..."    -> Prompts: "Command incomplete. Please repeat."
```

### 7. Language Mixing (Hindi-English Code-Switching)

```
"Roll number paanch ko marks do" -> "Roll 5 marks"
"Maths mein 90 de do" -> "Maths 90"
Hindi numbers: ek(1), do(2), teen(3), chaar(4), paanch(5)...
```

### 8. Repetition & Stuttering

- Filler words removed: "uh", "um", "er", "ah", "hmm"
- Consecutive duplicates deduplicated
- Last mentioned value used for repeated items

### 9. Contextual Ambiguity

- Missing context resolved via page URL
- Explicit requirements enforced per intent
- Clarifying questions when truly ambiguous

### 10. Speed & Timing

- Word gap timeout: 2 seconds
- Command timeout: 10 seconds
- Minimum audio: 0.5 seconds
- Maximum audio: 60 seconds

### 11. Accent Variations (Indian English)

- "Three" -> "Tree" (South India)
- "Five" -> "Phive" (North India)
- "Zero" -> "Jero"
- "th" sound variations handled

### 12. Command Structure Variations

All of these resolve to the same intent:
```
"Roll 1 maths 90 marks"
"Maths 90 for roll number 1"
"Give roll 1, 90 in maths"
"Student 1 mathematics ninety"
```

### 13. Error Recovery / Cancel

```
"Cancel" / "Cancel that" / "Undo" / "Go back"
"Delete that" / "Remove that" / "Never mind"
Hindi: "Nahi" / "Ruko" / "Band karo"
```

### 14. Batch Operation Mismatches

```
"questions 1, 2, 3, 4, 5 as 5, 6, 7"
-> 5 questions but only 3 marks
-> Returns BATCH_INCOMPLETE with partial results
-> User can "Confirm Partial" or fill missing values
```

### 15. Confirmation Voice Confusion

- Background "Yes sir" from student could false-trigger
- Specific phrases required: "confirm", "yes", "okay"
- 10-second timeout on confirmation listening
- Button click always available as fallback

---

## 8. Key Design Decisions

| Decision | Implementation | Rationale |
|----------|---------------|-----------|
| **Two-stage confirmation** | Preview -> User approves -> Execute | Prevents accidental data changes from voice misrecognition |
| **Live transcript preferred** | Web Speech API result used before Whisper | Faster (no model inference), Whisper only as fallback |
| **Regex-based NLP** | 4,000+ lines of hand-coded patterns | Works offline, no API costs, deterministic results |
| **Context from URL** | Frontend sends current page params | Disambiguates "mark all present" (which class?) |
| **Never HTTP 400** | Always 200 OK + CLARIFY intent | Better UX, frontend always gets structured displayable data |
| **Atomic transactions** | `@transaction.atomic` on all writes | No partial marks updates — all succeed or all fail |
| **localStorage for marks** | Cache + StorageEvent for cross-component sync | Instant UI updates without additional API calls |
| **Audit everything** | AuditLog on every CREATE/UPDATE/DELETE | Enables rollback, compliance, and accountability |
| **Voice confirmation** | Dialog also listens for "yes"/"no" voice | Hands-free workflow for classroom teachers |

---

## 9. Limitations of Current System

| Limitation | Current Implementation | Problem at Scale |
|-----------|----------------------|-----------------|
| **NLP Engine** | 4,000 lines of regex | Every new intent needs hundreds of new patterns. Unmaintainable beyond ~30 intents |
| **Whisper (local)** | Runs on server CPU/GPU | Slow on CPU (~5-10s for 30s audio). Needs dedicated GPU. Not scalable for 100+ concurrent users |
| **Web Speech API** | Chrome-only, requires internet | Doesn't work on Firefox/Safari reliably. Depends on Google servers |
| **Intent patterns** | Hard-coded English + some Hindi | Adding new languages = rewriting all 4,000 lines per language |
| **Entity extraction** | Custom regex per entity type | Fragile: "roll 5" works but "student number five" may not |
| **Normalization** | Hand-tuned for school vocabulary | "Create purchase order for vendor XYZ" has no patterns |
| **Single domain** | School marks / attendance / fees only | Cannot handle finance, HR, inventory, procurement without massive rewrite |
| **No streaming** | Upload full audio blob -> wait -> response | Long commands = long wait. No real-time word-by-word feedback |
| **Single database** | SQLite / single PostgreSQL | No multi-tenancy, no branch-level data isolation |
| **No conversation memory** | Each command is independent | Cannot handle "Now change roll 6 too" (no context from previous command) |
| **No offline support** | Requires server connection | Teachers in poor-connectivity areas cannot use |

---

## 10. Scaling for Complex ERP — What to Change

### Side-by-Side Comparison

```
CURRENT (Simple School)              COMPLEX ERP SYSTEM
========================             ====================

Browser Web Speech API               Deepgram / AssemblyAI Streaming API
(Chrome only, unreliable)        ->  (Real-time, all browsers, 40+ languages)

Local Whisper Model                  Whisper API (OpenAI) / Deepgram Cloud
(Slow, resource-hungry)          ->  (Cloud, fast, scalable, pay-per-use)

4,000-line Regex NLP                 LLM-based Intent Engine (Claude / GPT)
(Brittle, hard to extend)       ->  (Flexible, handles any phrasing naturally)

Hand-coded Entity Extraction         LLM Structured Output / Tool Use
(Fragile regex patterns)         ->  (Extract any entity from any sentence)

REST upload + wait                   WebSocket Streaming
(Full audio -> process -> respond)-> (Real-time transcription + processing)

Single PostgreSQL                    Multi-tenant PostgreSQL + Redis
(No isolation)                   ->  (Branch-level isolation, caching, pub/sub)

localStorage sync                    WebSocket Push + React Query
(Fragile, single-tab)           ->  (Real-time sync across all clients)

No conversation memory               Redis-backed Session Context
(Each command standalone)        ->  (Multi-turn: "Now do the same for roll 6")
```

---

## 11. Recommended Tech Stack for Complex ERP

### Speech-to-Text Layer

| Component | Current | Recommended | Why |
|-----------|---------|-------------|-----|
| **Primary STT** | Web Speech API | **Deepgram Streaming API** | Real-time, 40+ languages, all browsers, WebSocket-native, $0.0043/min |
| **Fallback STT** | Local Whisper | **OpenAI Whisper API** or **AssemblyAI** | No GPU needed, 99%+ accuracy, $0.006/min |
| **Audio Capture** | MediaRecorder | MediaRecorder + **Web Audio API** | Add noise suppression, VAD, gain control |

### NLP / Intent Engine

| Component | Current | Recommended | Why |
|-----------|---------|-------------|-----|
| **Intent Classification** | 4,000-line regex | **Claude Haiku / GPT-4o-mini** with structured output | Handles ANY phrasing, any language, zero regex maintenance |
| **Entity Extraction** | Custom regex | **LLM Tool Use / Function Calling** | Define tools per domain, LLM picks the right one automatically |
| **Normalization** | 8-step hand-coded pipeline | **LLM pre-processing** + minimal regex | LLM handles homophones, accents, code-switching natively |
| **Context Management** | URL params only | **Conversation Memory (Redis)** | Multi-turn: "Now change roll 6 too" remembers previous context |

**Example: LLM-based Intent Engine (replaces 4,000 lines of regex)**

```python
# ONE prompt replaces the entire regex engine:

SYSTEM_PROMPT = """
You are a voice command parser for a School ERP system.
Given a transcribed voice command + page context, return structured JSON.

Available intents and their required entities:
- UPDATE_MARKS: {roll_number, class, section, marks: {subject: value}}
- MARK_ATTENDANCE: {class, section, status, excluded_rolls?}
- COLLECT_FEE: {roll_number, amount, payment_method}
- CREATE_PURCHASE_ORDER: {vendor, items: [{name, qty, unit_price}]}
- APPROVE_LEAVE: {employee_id, leave_type, dates}
- ... (50+ intents defined as tool schemas)

If unclear, return intent: "CLARIFY" with a helpful message.
"""

response = client.messages.create(
    model="claude-haiku-4-5-20251001",
    system=SYSTEM_PROMPT,
    messages=[{"role": "user", "content": transcription}],
    tools=ERP_INTENT_TOOLS   # 50+ tool definitions
)
```

**Benefits:**
- Adding a new module (procurement, HR, inventory) = adding ONE tool definition
- No regex patterns to write or maintain
- Multilingual support works out of the box
- Handles any phrasing, accent, or sentence structure

### Real-Time Communication

| Component | Current | Recommended | Why |
|-----------|---------|-------------|-----|
| **Audio streaming** | Upload complete blob | **WebSocket + Deepgram** | Word-by-word transcript as user speaks |
| **Command feedback** | REST polling | **Django Channels + WebSocket** | Instant push, no polling overhead |
| **Multi-client sync** | localStorage + StorageEvent | **Redis Pub/Sub + WebSocket** | Teacher updates marks -> admin dashboard updates live |

### Backend Architecture

| Component | Current | Recommended | Why |
|-----------|---------|-------------|-----|
| **Framework** | Django 5.0 (sync only) | **Django 5.0 + Channels** (or separate FastAPI voice microservice) | WebSocket support, async processing |
| **Task Queue** | None | **Celery + Redis** | Offload STT, LLM calls, report generation |
| **Cache** | None | **Redis** | Cache STT results, user context, session state |
| **Database** | Single PostgreSQL | **PostgreSQL with multi-tenant schemas** | Branch-level data isolation |
| **Search** | None | **Elasticsearch** | Fuzzy search for students, vendors, items across all modules |

### Frontend Architecture

| Component | Current | Recommended | Why |
|-----------|---------|-------------|-----|
| **State Management** | Redux Toolkit | Redux Toolkit + **React Query** (TanStack Query) | Server state caching, auto-refetch, optimistic updates |
| **Voice UI** | FloatingVoiceButton | **Persistent voice panel + waveform visualizer** | Better UX for continuous dictation |
| **Real-time Sync** | localStorage events | **Socket.IO / native WebSocket** | Cross-tab, cross-user real-time updates |
| **Offline Support** | None | **Service Worker + IndexedDB** | Queue commands offline, sync when online |

---

## 12. Proposed Architecture Diagram

```
+-------------------------------------------------------------------+
|                      FRONTEND (React 18)                          |
|                                                                   |
|  +----------------+  +----------------+  +-----------------------+|
|  | Voice Panel    |  | WebSocket      |  | React Query Cache     ||
|  | (waveform,     |  | Client         |  | (marks, students,     ||
|  |  live text,    |  | (Socket.IO)    |  |  fees, inventory,     ||
|  |  confirmation) |  |                |  |  procurement)         ||
|  +-------+--------+  +-------+--------+  +-----------------------+|
|          |                    |                                    |
+----------+--------------------+------------------------------------+
           |                    |
     Audio Stream         Real-time events
           |                    |
           v                    v
+-------------------------------------------------------------------+
|                   API GATEWAY (nginx / Kong)                      |
+----------+--------------------+------------------------------------+
           |                    |
           v                    v
+------------------+  +------------------+  +----------------------+
| VOICE SERVICE    |  | MAIN ERP API     |  | WEBSOCKET SERVER     |
| (FastAPI or      |  | (Django DRF)     |  | (Django Channels)    |
|  Django async)   |  |                  |  |                      |
|                  |  | All CRUD APIs    |  | Push updates to      |
| 1. Deepgram      |  | for every module |  | all connected        |
|    Streaming STT |  |                  |  | clients              |
|                  |  | - Marks          |  |                      |
| 2. Claude Haiku  |  | - Attendance     |  |                      |
|    Intent Parse  |  | - Fees           |  |                      |
|    (Tool Use)    |  | - Procurement    |  |                      |
|                  |  | - HR / Leave     |  |                      |
| 3. Confirmation  |  | - Inventory      |  |                      |
|    Builder       |  | - Transport      |  |                      |
+--------+---------+  +--------+---------+  +----------+-----------+
         |                     |                        |
         v                     v                        v
+-------------------------------------------------------------------+
|              CELERY TASK QUEUE (Redis as broker)                   |
|                                                                   |
|  - Async STT processing       - Audit logging                    |
|  - LLM intent parsing         - Notification dispatch            |
|  - Report generation          - Bulk operations                  |
|  - Email / SMS / WhatsApp     - Data sync between modules        |
+-------------------------------------------------------------------+
         |                     |                        |
         v                     v                        v
+------------------+  +------------------+  +----------------------+
| PostgreSQL       |  | Redis            |  | Elasticsearch        |
| (multi-tenant,   |  | (cache, session, |  | (fuzzy search for    |
|  branch-level    |  |  pub/sub,        |  |  students, vendors,  |
|  schemas)        |  |  conversation    |  |  items, employees)   |
|                  |  |  memory)         |  |                      |
+------------------+  +------------------+  +----------------------+
```

---

## 13. Cost Comparison

### Current vs Proposed (for ~1000 daily active users)

| Component | Current Monthly Cost | Proposed Monthly Cost |
|-----------|---------------------|----------------------|
| **Whisper (local GPU server)** | ~$200 (GPU instance) | $0 (eliminated) |
| **Deepgram STT API** | $0 | ~$50-150 (streaming) |
| **Claude Haiku (intent parsing)** | $0 | ~$20-50 |
| **OpenAI Whisper API (fallback)** | $0 | ~$10-30 |
| **Web Speech API** | Free | $0 (eliminated) |
| **Redis** | $0 | ~$15-30 |
| **Elasticsearch** | $0 | ~$30-50 |
| **Current GPU Total** | **~$200/mo** | — |
| **Proposed Cloud Total** | — | **~$125-310/mo** |

> The cloud approach is **comparable or cheaper** than maintaining a GPU server, while being **far more scalable** and **reliable**.

---

## 14. Migration Priority

| Priority | Change | Effort | Impact |
|----------|--------|--------|--------|
| **1 (Critical)** | Replace regex NLP with Claude Haiku tool_use | 1-2 weeks | Unlocks ALL new modules without writing regex. Single biggest ROI change. |
| **2 (High)** | Replace Web Speech API with Deepgram streaming | 1 week | Works on all browsers, better accuracy, real-time word-by-word |
| **3 (High)** | Add WebSocket via Django Channels | 1 week | Multi-user real-time sync, instant confirmation push |
| **4 (Medium)** | Add Celery + Redis for async processing | 3-4 days | Handle concurrent users, non-blocking voice processing |
| **5 (Medium)** | Add Redis for conversation context | 2-3 days | Multi-turn commands ("Now do the same for roll 6") |
| **6 (Low)** | Add Elasticsearch for fuzzy entity search | 1 week | Better entity resolution across all modules |
| **7 (Low)** | Add offline support (Service Worker) | 1 week | Queue commands in poor connectivity areas |

### The Single Most Important Change

> **Replace the 4,000-line regex engine with LLM-based intent parsing.**
> This alone eliminates ~80% of the scaling pain. Every new ERP module becomes a tool definition instead of hundreds of regex patterns.

---

## 15. File Reference

### Backend Files

| File | Purpose | Size |
|------|---------|------|
| `backend/apps/voice_processing/intent_extractor.py` | NLP engine (normalization + intent + entity extraction) | 165 KB, 4000+ lines |
| `backend/apps/voice_processing/command_executor.py` | Command execution (DB writes) | 76 KB |
| `backend/apps/voice_processing/views.py` | API endpoints for voice upload/confirm/reject | 31 KB |
| `backend/apps/voice_processing/speech_to_text.py` | Whisper STT integration | ~5 KB |
| `backend/apps/voice_processing/models.py` | VoiceCommand model | ~3 KB |
| `backend/apps/voice_processing/urls.py` | Voice API URL routing | ~1 KB |
| `backend/apps/authentication/models.py` | CustomUser, Teacher models | ~5 KB |
| `backend/apps/marks/models.py` | Marks, QuestionWiseMarks models | ~4 KB |
| `backend/apps/marks/views.py` | Marks CRUD API | ~8 KB |
| `backend/apps/attendance/models.py` | AttendanceSession, AttendanceRecord | ~3 KB |
| `backend/apps/academics/models.py` | Class, Section, Student, Subject | ~5 KB |
| `backend/apps/fees/models.py` | FeeTransaction model | ~3 KB |
| `backend/apps/audit/models.py` | AuditLog model | ~2 KB |
| `backend/config/settings/base.py` | Django settings | ~5 KB |
| `backend/config/urls.py` | Root URL configuration | ~2 KB |
| `backend/requirements/base.txt` | Python dependencies | ~2 KB |

### Frontend Files

| File | Purpose | Size |
|------|---------|------|
| `frontend/src/components/voice/ConfirmationDialog.jsx` | Confirmation UI with 12+ preview types | 1200+ lines |
| `frontend/src/components/voice/FloatingVoiceButton.jsx` | Floating mic button + recorder + upload | ~400 lines |
| `frontend/src/components/voice/VoiceReceiptModal.jsx` | Fee receipt display/print | ~200 lines |
| `frontend/src/hooks/useVoiceRecorder.js` | MediaRecorder audio capture hook | ~80 lines |
| `frontend/src/hooks/useSpeechRecognition.js` | Web Speech API live transcript hook | ~100 lines |
| `frontend/src/services/voiceService.js` | Voice API service (upload, confirm, reject) | ~80 lines |
| `frontend/src/services/api.js` | Axios instance with JWT interceptors | ~60 lines |
| `frontend/src/store/slices/voiceSlice.js` | Voice Redux state management | ~80 lines |
| `frontend/src/store/slices/authSlice.js` | Auth Redux state + localStorage | ~60 lines |
| `frontend/src/store/slices/uiSlice.js` | UI state (dialogs, notifications) | ~40 lines |
| `frontend/src/pages/MarksSheetPage.jsx` | Marks table with localStorage sync | ~300 lines |
| `frontend/src/pages/QuestionWisePage.jsx` | Question-wise marks entry | ~400 lines |
| `frontend/src/App.jsx` | Routing + auth setup | ~150 lines |
| `frontend/package.json` | Dependencies | ~1 KB |

### API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `POST` | `/api/v1/voice/upload/` | Upload audio + get intent + confirmation data |
| `POST` | `/api/v1/voice/commands/{id}/confirm/` | Execute confirmed command |
| `POST` | `/api/v1/voice/commands/{id}/reject/` | Reject/cancel command |
| `GET` | `/api/v1/voice/commands/` | List user's command history |
| `POST` | `/api/v1/auth/login/` | JWT login |
| `POST` | `/api/v1/auth/token/refresh/` | Refresh JWT token |
| `GET` | `/api/v1/academics/classes/` | List classes |
| `GET` | `/api/v1/academics/students/` | List students |
| `GET/POST` | `/api/v1/marks/marks-list/` | Get/create marks |
| `PUT` | `/api/v1/marks/{id}/update-marks/` | Update marks |
| `POST` | `/api/v1/marks/batch-update/` | Batch update marks |
| `GET` | `/api/v1/marks/question-wise-marks/` | Get question-wise marks |
| `GET/POST` | `/api/v1/attendance/records/` | Get/create attendance |
| `PUT` | `/api/v1/attendance/{id}/update/` | Update attendance record |

---

## Test Coverage

- **20 unit tests** — all passing
- **File:** `backend/apps/voice_processing/tests/test_intelligent_normalization.py`
- Covers: smart number splitting, range expansion, decimal preservation, batch parsing, separator normalization, real-world fast speech scenarios

---

*Generated: February 2026*
