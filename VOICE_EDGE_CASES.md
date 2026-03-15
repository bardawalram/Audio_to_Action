# Voice Command System - Edge Cases & Handling Guide

This document outlines all potential edge cases for the Audio-to-Action voice command system used in classroom environments for school ERP operations.

---

## Table of Contents

1. [Homophones & Similar Sounds](#1-homophones--similar-sounds)
2. [Subject Name Mishearings](#2-subject-name-mishearings)
3. [Number Confusion](#3-number-confusion)
4. [Mid-Sentence Corrections](#4-mid-sentence-corrections)
5. [Background Noise Scenarios](#5-background-noise-scenarios)
6. [Incomplete/Interrupted Commands](#6-incompleteinterrupted-commands)
7. [Language Mixing (Code-Switching)](#7-language-mixing-code-switching)
8. [Repetition & Stuttering](#8-repetition--stuttering)
9. [Contextual Ambiguity](#9-contextual-ambiguity)
10. [Speed & Timing Issues](#10-speed--timing-issues)
11. [Accent Variations](#11-accent-variations)
12. [Command Structure Variations](#12-command-structure-variations)
13. [Error Recovery Scenarios](#13-error-recovery-scenarios)
14. [Batch Operation Edge Cases](#14-batch-operation-edge-cases)
15. [Confirmation Confusion](#15-confirmation-confusion)
16. [Technical Issues](#16-technical-issues)
17. [Semantic Ambiguity](#17-semantic-ambiguity)
18. [Question-Wise Marks Edge Cases](#18-question-wise-marks-edge-cases)
19. [Attendance-Specific Edge Cases](#19-attendance-specific-edge-cases)
20. [Navigation Edge Cases](#20-navigation-edge-cases)

---

## 1. Homophones & Similar Sounds

Words that sound identical or very similar but have different meanings.

| Spoken | Misheard As | Context | Impact |
|--------|-------------|---------|--------|
| "to" | "2" | "update marks to 90" | Interpreted as "update marks 2 90" |
| "for" | "4" | "marks for roll 1" | Interpreted as "marks 4 roll 1" |
| "one" | "won" | "roll one" | May not recognize as number |
| "two" | "to" / "too" | "roll two" | May not recognize as number |
| "four" | "for" | "roll four" | May interpret as preposition |
| "eight" | "ate" | "question eight" | May not recognize |
| "roll" | "role" / "rule" | "roll number 5" | Common STT variation |
| "marks" | "max" / "marx" | "update marks" | Intent detection fails |

### Recommended Handling
```python
# Normalize homophones in context
homophones = {
    'won': '1', 'too': '2', 'to': '2',  # Only in numeric context
    'for': '4',  # Only after "roll" or before numbers
    'ate': '8',
    'rule': 'roll', 'role': 'roll',
}
```

---

## 2. Subject Name Mishearings

Common speech recognition errors for subject names.

| Subject | Common Mishearings | Frequency |
|---------|-------------------|-----------|
| Mathematics / Maths | "mass", "match", "moths", "max", "mats" | High |
| Hindi | "indy", "indie", "hind", "hendy" | Medium |
| English | "in glitch", "ang lish", "enlist" | Low |
| Science | "signs", "silence", "sigh ants" | Medium |
| Social Studies | "so shall", "social studied", "so shell" | Medium |
| Computer | "compote", "come pewter", "computer" | Low |
| Physical Education | "physical head", "PE" | Low |

### Recommended Handling
```python
subject_fuzzy_match = {
    'mass': 'MATH', 'match': 'MATH', 'moths': 'MATH', 'mats': 'MATH',
    'indy': 'HINDI', 'indie': 'HINDI', 'hind': 'HINDI',
    'signs': 'SCIENCE', 'silence': 'SCIENCE',
    'so shall': 'SOCIAL', 'so shell': 'SOCIAL',
}
```

---

## 3. Number Confusion

Critical for marks entry - wrong number = wrong marks.

### 3.1 Teen vs Ty Confusion
| Intended | Misheard | Example |
|----------|----------|---------|
| 15 (fifteen) | 50 (fifty) | "Student got fifteen" → 50 |
| 13 (thirteen) | 30 (thirty) | "Roll thirteen" → Roll 30 |
| 14 (fourteen) | 40 (forty) | "Marks fourteen" → 40 |
| 16 (sixteen) | 60 (sixty) | Critical mark difference |
| 17 (seventeen) | 70 (seventy) | Critical mark difference |
| 18 (eighteen) | 80 (eighty) | Critical mark difference |
| 19 (nineteen) | 90 (ninety) | Critical mark difference |

### 3.2 Similar Sounding Numbers
| Pair | Context |
|------|---------|
| 90 vs 19 | Both common marks values |
| 80 vs 18 | Both common marks values |
| 70 vs 17 | Both common marks values |

### 3.3 Decimal Confusion
| Spoken | Interpreted As |
|--------|---------------|
| "seven point five" | 7.5 (correct) |
| "seven five" | 75 or 7, 5 |
| "seventy five" | 75 |

### 3.4 Concatenated Numbers
| Spoken | Possible Interpretations |
|--------|------------------------|
| "one two three four five" | 1,2,3,4,5 or 12345 |
| "twelve thirty four" | 12, 34 or 1234 |

### Recommended Handling
- Validate marks are within expected range (0-100)
- Flag unusual values (marks > subject max)
- Confirm values that seem out of pattern

---

## 4. Mid-Sentence Corrections

Teachers often correct themselves while speaking.

### Common Correction Patterns
```
"Update maths marks... no wait, science marks 90"
"Roll 5 gets 80... sorry, roll 6 gets 80"
"Mathematics 100... actually make it 90"
"Mark all present except... no, mark all absent"
"Question 3 is 8... I mean question 4 is 8"
"Hindi 90... sorry, I meant English 90"
```

### Correction Keywords to Detect
| Keyword | Action |
|---------|--------|
| "sorry" | Discard previous value |
| "no wait" | Discard previous command |
| "actually" | Replace previous value |
| "I mean" / "I meant" | Replace previous value |
| "not that" | Discard previous |
| "correction" | Replace previous |
| "instead" | Replace previous value |
| "change that to" | Replace previous |

### Recommended Handling
```python
correction_keywords = [
    'sorry', 'no wait', 'actually', 'i mean', 'i meant',
    'not that', 'correction', 'instead', 'change that to',
    'wait', 'hold on', 'scratch that', 'ignore that'
]
```

---

## 5. Background Noise Scenarios

Classroom environments are inherently noisy.

### 5.1 Human Noise Sources
| Source | Characteristics | Impact |
|--------|----------------|--------|
| Students talking | Multiple overlapping voices | Words from wrong speaker captured |
| Student answering | Clear single voice | May be captured as command |
| Other teacher | Adult voice nearby | Confuses speaker identification |
| Students laughing | Burst of noise | Interrupts command |

### 5.2 Environmental Noise
| Source | Characteristics | Impact |
|--------|----------------|--------|
| School bell | Loud, sudden | Cuts off command |
| PA announcement | Clear speech | Overlaps with command |
| Fan/AC | Continuous hum | Reduces clarity |
| Traffic | Intermittent | Random noise injection |
| Door sounds | Sudden bang | Startles, interrupts |
| Chair scraping | High-pitched | Distorts audio |

### 5.3 Electronic Noise
| Source | Characteristics |
|--------|----------------|
| Mobile phone | Notification sounds |
| Computer alerts | System sounds |
| Projector fan | Continuous hum |

### Recommended Handling
- Implement noise gate (minimum volume threshold)
- Use voice activity detection (VAD)
- Require wake word or button press to start
- Show real-time transcription for verification

---

## 6. Incomplete/Interrupted Commands

Commands that don't complete properly.

### Common Scenarios
```
"Update marks for roll..." (teacher gets distracted)
"Mark attendance for class..." (student asks question)
"Question 3 is..." (phone rings)
"Roll number 5 gets..." (another teacher calls)
"Mathematics marks for..." (bell rings)
```

### Detection Criteria
| Pattern | Status |
|---------|--------|
| Command verb + incomplete object | Incomplete |
| Number expected but not received | Incomplete |
| Subject mentioned but no marks | Incomplete |
| "for" at end of sentence | Incomplete |

### Recommended Handling
- Detect trailing prepositions ("for", "to", "of")
- Timeout after 3 seconds of silence
- Prompt user: "Command incomplete. Please repeat."
- Store partial command for potential completion

---

## 7. Language Mixing (Code-Switching)

Teachers often mix Hindi/regional language with English.

### Common Hindi-English Mixing
| Mixed Command | Meaning |
|---------------|---------|
| "Roll number paanch ko marks do" | Give marks to roll 5 |
| "Maths mein 90 de do" | Give 90 in Maths |
| "Ek, do, teen ko present mark karo" | Mark 1, 2, 3 as present |
| "Sab ko absent kar do except roll das" | Mark all absent except roll 10 |
| "Question chaar mein aath marks" | 8 marks in question 4 |

### Hindi Number Words
| Hindi | English | Number |
|-------|---------|--------|
| ek | one | 1 |
| do | two | 2 |
| teen | three | 3 |
| chaar | four | 4 |
| paanch | five | 5 |
| chhe | six | 6 |
| saat | seven | 7 |
| aath | eight | 8 |
| nau | nine | 9 |
| das | ten | 10 |

### Recommended Handling
```python
hindi_numbers = {
    'ek': 1, 'do': 2, 'teen': 3, 'chaar': 4, 'paanch': 5,
    'chhe': 6, 'saat': 7, 'aath': 8, 'nau': 9, 'das': 10,
    'gyarah': 11, 'barah': 12, 'terah': 13, 'chaudah': 14, 'pandrah': 15,
    'solah': 16, 'satrah': 17, 'atharah': 18, 'unnis': 19, 'bees': 20,
}
```

---

## 8. Repetition & Stuttering

Natural speech patterns that can confuse parsing.

### Common Patterns
| Pattern | Example |
|---------|---------|
| Word repetition | "Roll 5, roll 5, marks 90" |
| Command repetition | "Update update marks" |
| Filler words | "Uh... um... roll number 3" |
| Self-echo | "Ninety, ninety marks" |
| Thinking aloud | "Let me see... roll 5... yes, roll 5" |

### Filler Words to Filter
```
uh, um, er, ah, hmm, let me see, okay so,
well, like, you know, basically, actually (without correction context)
```

### Recommended Handling
- Remove filler words before processing
- Deduplicate consecutive identical values
- Use last mentioned value for repeated items

---

## 9. Contextual Ambiguity

Commands that depend on unstated context.

### Ambiguous Commands
| Command | Ambiguity |
|---------|-----------|
| "Same as before" | What was "before"? |
| "Give him 90" | Who is "him"? |
| "Mark everyone" | Which class? |
| "Update the marks" | Which student? Which subject? |
| "Next student" | Based on what ordering? |
| "Previous one" | Previous what? |
| "That student" | Which one? |
| "All subjects" | Which subjects are "all"? |

### Context Dependencies
| Missing Context | Required From |
|-----------------|--------------|
| Class/Section | Current page URL |
| Student | Roll number or selection |
| Subject | Page context or explicit mention |
| Exam type | Session default or explicit |
| Date (attendance) | Current date or explicit |

### Recommended Handling
- Always use page context as fallback
- Require explicit values for critical fields
- Ask clarifying questions when ambiguous
- Never assume - confirm with user

---

## 10. Speed & Timing Issues

Speaking pace affects recognition accuracy.

### Too Fast
```
"rollonemathninetyhindieigtyfive"
→ Merged words, hard to parse
→ Numbers run together
```

### Too Slow
```
"Roll... [5 second pause]... one"
→ May be detected as two separate commands
→ Timeout between words
```

### Uneven Pacing
```
"Roll one [pause] MATHSNINETYHINDIEIGNTY"
→ First part clear, second part rushed
→ Numbers spoken faster than words
```

### Timing Thresholds
| Parameter | Recommended Value |
|-----------|------------------|
| Word gap timeout | 2 seconds |
| Command timeout | 10 seconds |
| Minimum audio length | 0.5 seconds |
| Maximum audio length | 60 seconds |

---

## 11. Accent Variations

Indian English accent variations affect recognition.

### Common Variations
| Standard | Regional Variation | Region |
|----------|-------------------|--------|
| "Three" | "Tree" | South India |
| "Thirty" | "Tirty" | General |
| "Five" | "Phive" | North India |
| "Zero" | "Jero" | General |
| "Very" | "Wery" | Some regions |
| "One" | "Van" / "Von" | Some regions |
| "Marks" | "Maarks" | General |

### V/W Confusion
| Word | May sound like |
|------|---------------|
| "View" | "Wiew" |
| "Very" | "Wery" |
| "Five" | "Phive" |

### Th Sound Variations
| Word | May sound like |
|------|---------------|
| "Three" | "Tree" |
| "Thirty" | "Tirty" |
| "Thirteen" | "Tirteen" |

---

## 12. Command Structure Variations

Same intent can be expressed many ways.

### "Update marks for roll 1, maths 90"
All these should work:
```
"Update marks for roll 1 maths 90"
"Roll 1 maths 90 marks"
"Maths 90 for roll number 1"
"Give roll 1, 90 in maths"
"Student 1 mathematics ninety"
"Roll number one, maths marks ninety"
"For roll 1, update maths to 90"
"Maths marks 90 roll 1"
```

### "Mark all students present"
```
"Mark all present"
"Everyone present"
"All students are present"
"Mark attendance - all present"
"Present for all"
"Sab present hai" (Hindi)
```

### Subject-Marks Order Variations
```
"Maths 90 Hindi 80"      (Subject first)
"90 in Maths, 80 in Hindi" (Marks first)
"90 marks in Mathematics"  (Marks + subject)
"Mathematics: 90, Hindi: 80" (With colons)
```

---

## 13. Error Recovery Scenarios

How users try to fix mistakes.

### Cancel/Undo Commands
```
"Cancel" / "Cancel that"
"Undo" / "Undo that"
"Go back"
"Delete that"
"Remove that"
"Never mind"
"Forget it"
"Stop"
```

### Correction Commands
```
"That's wrong"
"Not that"
"I said 90, not 19"
"Wrong student"
"Wrong subject"
"Change it to 85"
"Make it 90 instead"
```

### Confirmation Responses
| Positive | Negative |
|----------|----------|
| "Yes" | "No" |
| "Correct" | "Wrong" |
| "Confirm" | "Cancel" |
| "That's right" | "That's wrong" |
| "Proceed" | "Stop" |
| "Okay" | "Wait" |
| "Haan" (Hindi) | "Nahi" (Hindi) |

---

## 14. Batch Operation Edge Cases

Operations affecting multiple items.

### Parallel List Mismatches
```
"Questions 1, 2, 3, 4, 5 as 8, 7, 9"
→ 5 questions but only 3 marks
→ How to handle mismatch?
```

### Range Specifications
```
"Questions 1 to 10 all get 8 marks"
→ Range with uniform value

"Roll 1 to 5 present, 6 to 10 absent"
→ Multiple ranges with different values

"Questions 1 through 5, marks 8, 7, 9, 6, 10"
→ Range + parallel marks
```

### Exclusion Patterns
```
"All present except roll 5"
"Everyone except 3 and 7"
"Mark all except absent students"
"All subjects except PE"
```

### Batch Validation
- Count of items in each list should match
- Validate all values are within range
- Confirm before bulk operations
- Show preview of all changes

---

## 15. Confirmation Confusion

Background voices can trigger false confirmations.

### False Positive Triggers
| Intended | May be heard from background |
|----------|------------------------------|
| "Yes" | Student saying "Yes sir" |
| "Okay" | Casual conversation |
| "Confirm" | Unrelated discussion |
| "Right" | "Right answer!" from student |

### False Negative Triggers
| Intended | May be misheard as |
|----------|-------------------|
| "Yes" | "Guess" |
| "No" | "Know" / "Go" |
| "Confirm" | "Can form" |
| "Cancel" | "Can sell" |

### Recommended Handling
- Require specific confirmation phrase
- Use button confirmation for critical actions
- Add visual confirmation step
- Timeout confirmation after 10 seconds

---

## 16. Technical Issues

Hardware and software problems.

### Microphone Issues
| Issue | Symptom |
|-------|---------|
| Low volume | Partial or no recognition |
| Too close | Distorted, clipped audio |
| Too far | Weak signal, background noise dominant |
| Muted | No audio captured |
| Wrong device | System mic vs headset |

### Browser Issues
| Issue | Impact |
|-------|--------|
| Permission denied | Cannot record |
| Unsupported browser | Web Speech API unavailable |
| Tab inactive | Recording may pause |
| Memory pressure | Slow processing |

### Network Issues
| Issue | Impact |
|-------|--------|
| High latency | Delayed response |
| Connection drop | Command lost |
| Timeout | Partial processing |

### Audio Quality Issues
| Issue | Cause |
|-------|-------|
| Compression artifacts | Low bitrate |
| Clipping | Volume too high |
| Echo | Speaker feedback |
| Noise floor | Poor mic quality |

---

## 17. Semantic Ambiguity

Logically confusing commands.

### Contradictory Commands
```
"Mark all present except the absent ones"
→ Logically redundant

"Give 90 marks but not more than 80"
→ Contradictory values

"Update roll 5 and roll 5"
→ Duplicate reference
```

### Scope Ambiguity
```
"Give 90 to all subjects"
→ All subjects for one student?
→ Or one subject for all students?

"Mark everyone in all classes"
→ All students in current class?
→ Or literally all classes?
```

### Temporal Ambiguity
```
"Mark attendance for yesterday"
→ Can we modify past records?

"Same marks as last exam"
→ Which exam was "last"?
```

---

## 18. Question-Wise Marks Edge Cases

Specific to question-level marking.

### Question Number Issues
```
"Question 1A" → Sub-questions
"Question 1.1" → Decimal notation
"Question 1 part 2" → Parts
"Bonus question" → Unnumbered
```

### Marks Distribution
```
"Question 1 is 8 out of 10"
→ Both obtained and max marks

"Half marks for question 3"
→ Relative to max marks

"Full marks for all"
→ Need to know max for each
```

### Partial Marks
```
"7.5 marks" → Decimal support needed
"Seven and a half" → Word form
"Half of 10" → Calculation needed
```

---

## 19. Attendance-Specific Edge Cases

### Status Variations
| Standard | Variations |
|----------|------------|
| Present | "Here", "Attending", "In class" |
| Absent | "Not here", "Missing", "Away" |
| Late | "Tardy", "Came late", "Delayed" |
| Half-day | "Left early", "Came late" |

### Bulk Operations
```
"First 10 rolls present, rest absent"
"Only girls present today"
"Everyone except medical leave"
```

### Time-Sensitive
```
"Mark late for roll 5"
→ Need timestamp

"Changed from absent to present"
→ Correction after initial marking
```

---

## 20. Navigation Edge Cases

Moving between pages.

### Ambiguous Destinations
```
"Open marks" → List page or entry page?
"Go to class 5" → Which section? Which module?
"Show student" → Which student?
```

### Section Naming
```
"Class 1A" vs "Class 1 A" vs "Class 1 Section A"
"First A" vs "1st A" vs "One A"
"Class one alpha" → "1A"
```

### Module Confusion
```
"Open attendance marks" → Attendance or Marks?
"Marks attendance" → ?
```

---

## Implementation Priority

### High Priority (Must Fix)
1. Homophone handling (to/2, for/4)
2. Subject name fuzzy matching
3. Number normalization (15 vs 50)
4. Mid-sentence corrections (sorry, actually)
5. Context from page URL

### Medium Priority (Should Fix)
6. Hindi number support
7. Filler word removal
8. Incomplete command detection
9. Confirmation safety
10. Error recovery commands

### Low Priority (Nice to Have)
11. Accent variation handling
12. Full Hindi command support
13. Predictive suggestions
14. Voice identification (which teacher)
15. Noise cancellation

---

## Testing Checklist

### Basic Commands
- [ ] Simple marks entry
- [ ] Simple attendance marking
- [ ] Navigation commands
- [ ] Question-wise marks

### Edge Cases
- [ ] Homophones (to/2, for/4)
- [ ] Subject mishearings
- [ ] Number confusion (15/50)
- [ ] Mid-sentence corrections
- [ ] Incomplete commands
- [ ] Background noise handling

### Batch Operations
- [ ] Parallel list matching
- [ ] Range specifications
- [ ] Exclusion patterns

### Error Recovery
- [ ] Cancel/Undo
- [ ] Corrections
- [ ] Confirmation flow

---

## Appendix: Test Phrases

### Marks Entry Test Cases
```
1. "Update marks for roll 1 maths 90 hindi 80"
2. "Student 5 mathematics fifty" (should be 50, not 15)
3. "Roll to gets for marks" (2 gets 4 marks)
4. "Update maths... sorry science 90 for roll 3"
5. "Mass ninety for rule one" (Maths 90 for roll 1)
```

### Attendance Test Cases
```
1. "Mark all present"
2. "Everyone present except roll 5"
3. "Roll ek do teen absent" (1, 2, 3 in Hindi)
4. "Mark attendance... actually cancel that"
5. "Present for... no wait, absent for roll 7"
```

### Question Marks Test Cases
```
1. "Question 1 is 8"
2. "Questions 1 2 3 as 8 7 9"
3. "For question ate give ate" (8 give 8)
4. "Question one to five all get 10"
5. "Update question 3... sorry 4 to 7 marks"
```

---

*Document Version: 1.0*
*Last Updated: January 2026*
*System: Audio-to-Action Voice Command System*
