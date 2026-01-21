"""
Intent and entity extraction from transcribed text.
Uses regex patterns for parsing voice commands.
"""
import re
import logging

logger = logging.getLogger(__name__)


class IntentExtractor:
    """
    Extracts intent from transcribed text using regex patterns.
    """

    # Intent patterns - Order matters! More specific patterns first
    # Check patterns from most specific to least specific
    INTENT_PATTERNS = {
        # Batch question marks update (MUST be before single UPDATE_QUESTION_MARKS)
        'BATCH_UPDATE_QUESTION_MARKS': [
            # MOST FLEXIBLE: questions followed by many numbers (10+ digits total suggests batch)
            r'questions?\s+(?:\d+[\s,]+){5,}\d+',  # "questions 1 2 3 4 5 6 7 8 9 10" (6+ numbers)
            # Parallel list pattern with "as" keyword (most explicit) - REQUIRE 3+ numbers before "as"
            r'questions?\s+\d+\s*,\s*\d+\s*,\s*\d+.*(?:as|give)',  # "questions 1, 2, 3 as 4, 5, 6" (3+ before "as")
            r'questions?\s+\d+\s+\d+\s+\d+.*(?:as|give)',  # "questions 1 2 3 as 4 5 6" (3+ numbers)
            # Without "as" but with commas (clearly a list) - REQUIRE 3+ commas
            r'questions?\s+\d+\s*,\s*\d+\s*,\s*\d+\s*,\s*\d+',  # "questions 1, 2, 3, 4, 5" (4+ numbers)
            # Batch patterns - look for multiple question-marks pairs
            r'(?:update|change|set)\s+(?:marks?\s+)?(?:for\s+)?questions?.*(?:question|,|\d+\s+(?:marks?|is)).*(?:question|,)',  # Must have multiple questions
            # FLEXIBLE: Allow commas after question numbers - "for question 1, give 5"
            r'(?:for\s+)?(?:question\s+)?\d+[\s,]+(?:give|is|marks?)\s+\d+.*(?:for|question).*\d+[\s,]+(?:give|is|marks?)',  # "for question 1, give 5, for question 2, give 7"
            r'question\s+\d+\s+is\s+\d+.*question',  # "question 1 is 3, question 2 is 5"
        ],
        # Question-wise marks (MUST be before UPDATE_MARKS)
        'UPDATE_QUESTION_MARKS': [
            # Full patterns with subject and roll
            r'update\s+(?:the\s+)?(?:maths?|mathematics|hindi|english|science|social\s*(?:studies)?|computer)\s+question\s+(?:number\s+|no\.?\s+|#)?(\d+)\s+(?:for\s+|of\s+)?(?:roll|rule)\s+(?:number\s+|no\.?\s+|#)?(\d+)',
            r'update\s+question\s+(?:number\s+|no\.?\s+|#)?(\d+)\s+(?:for\s+|of\s+)?(?:maths?|mathematics|hindi|english|science|social\s*(?:studies)?|computer)\s+(?:for\s+|of\s+)?(?:roll|rule)\s+(?:number\s+|no\.?\s+|#)?(\d+)',
            r'(?:set|change|give|put)\s+(?:maths?|mathematics|hindi|english|science|social\s*(?:studies)?|computer)\s+question\s+(?:number\s+|no\.?\s+|#)?(\d+)\s+(?:for\s+|of\s+)?(?:roll|rule)\s+(?:number\s+|no\.?\s+|#)?(\d+)',
            # NEW: "for question X give Y" format (SINGLE question only - note: batch pattern requires 2+ pairs)
            r'for\s+question\s+(?:number\s+|no\.?\s+|#)?(\d+)[\s,]+give\s+(\d+(?:\.\d+)?)\s*(?:marks?)?',
            # Short patterns (when on QuestionWisePage with context)
            r'update\s+(?:the\s+)?question\s+(?:number\s+|no\.?\s+|#)?(\d+)\s+(?:to|with|as)\s+(\d+(?:\.\d+)?)\s*(?:marks?|points?)?',
            r'(?:set|change|give|put|mark)\s+(?:the\s+)?question\s+(?:number\s+|no\.?\s+|#)?(\d+)\s+(?:to|as|at)\s+(\d+(?:\.\d+)?)\s*(?:marks?|points?)?',
            r'question\s+(?:number\s+|no\.?\s+|#)?(\d+)\s+(?:to|as|should\s+be)\s+(\d+(?:\.\d+)?)\s*(?:marks?|points?)?',
            # "question X marks Y" or "question X Y marks" format
            r'(?:update\s+)?question\s+(?:number\s+|no\.?\s+|#)?(\d+)\s+(?:marks?\s+)?(\d+(?:\.\d+)?)\s*(?:marks?)?',
            # Even simpler: "question 3 8" or "question 3 as 8"
            r'(?:update\s+)?question\s+(\d+)\s+(?:as\s+|/\s*)?(\d+(?:\.\d+)?)',
            # VERY FLEXIBLE: "change/update question X Y" (no connector word)
            r'(?:change|update|set)\s+question\s+(?:number\s+|no\.?\s+|#)?(\d+)\s+(\d+(?:\.\d+)?)',
            # "change question X marks Y" (marks before number)
            r'(?:change|update|set)\s+question\s+(?:number\s+|no\.?\s+|#)?(\d+)\s+marks?\s+(\d+(?:\.\d+)?)',
        ],
        # Attendance marking (MUST be first to catch "marks attendance" before "marks")
        'MARK_ATTENDANCE': [
            r'marks?\s+attendance',  # "marks attendance for class..." - MUST be first!
            r'mark\s+(?:the\s+)?attendance',
            r'take\s+(?:the\s+)?attendance',
            r'attendance\s+for\s+class',
            r'mark\s+(?:everyone|all|students?)\s+(?:as\s+)?present',
            r'mark\s+(?:everyone|all|students?)\s+(?:as\s+)?absent',
            r'mark\s+(?:all|everyone)\s+(?:as\s+)?present\s+except',
            r'mark\s+class\s+\d+\s*[a-z]?\s+(?:as\s+)?present',
        ],
        # Update marks (before ENTER_MARKS and navigation)
        'UPDATE_MARKS': [
            r'update[\.\s]+(?:the\s+)?marks?[\.\s]+(?:for\s+|of\s+|to\s+)?(?:roll|rule)[\.\s]+(?:number\s+|no\.?\s+|#|to\s+)?(\d+)',
            r'update[\.\s]+(?:the\s+)?marks?[\.\s]+(?:roll|rule)[\.\s]+(?:to|for|number)?\s*(\d+)',
            r'change[\.\s]+(?:the\s+)?marks?[\.\s]+(?:for\s+|of\s+|to\s+)?(?:roll|rule)[\.\s]+(?:number\s+|no\.?\s+|#)?(\d+)',
            r'modify[\.\s]+(?:the\s+)?marks?[\.\s]+(?:for\s+|of\s+)?(?:roll|rule)[\.\s]+(?:number\s+|no\.?\s+|#)?(\d+)',
            r'set[\.\s]+(?:the\s+)?marks?[\.\s]+(?:for\s+|of\s+)?(?:roll|rule)[\.\s]+(?:number\s+|no\.?\s+|#)?(\d+)',
        ],
        # Marks entry (before navigation)
        'ENTER_MARKS': [
            r'enter\s+(?:the\s+)?marks?\s+for\s+(?:roll|rule)',
            r'add\s+(?:the\s+)?marks?\s+for\s+(?:roll|rule)',
            r'put\s+(?:the\s+)?marks?\s+for\s+(?:roll|rule)',
            r'give\s+(?:the\s+)?marks?\s+for\s+(?:roll|rule)',
            r'submit\s+(?:the\s+)?marks?\s+for\s+(?:roll|rule)',
        ],
        # Open question-wise marksheet (MUST be before OPEN_MARKS_SHEET)
        'OPEN_QUESTION_SHEET': [
            r'open\s+(?:the\s+)?question[\s-]?wise\s+(?:marks?|marksheet)\s+(?:for\s+|of\s+)?(?:roll|rule)\s+(?:number\s+|no\.?\s+|#)?(\d+)\s+(?:maths?|mathematics|hindi|english|science|social|computer)',
            r'show\s+(?:the\s+)?question[\s-]?wise\s+(?:marks?|marksheet)\s+(?:for\s+|of\s+)?(?:roll|rule)\s+(?:number\s+|no\.?\s+|#)?(\d+)\s+(?:maths?|mathematics|hindi|english|science|social|computer)',
            r'go\s+to\s+(?:the\s+)?question[\s-]?wise\s+(?:marks?|marksheet|page)\s+(?:for\s+|of\s+)?(?:roll|rule)\s+(?:number\s+|no\.?\s+|#)?(\d+)\s+(?:maths?|mathematics|hindi|english|science|social|computer)',
        ],
        # Specific class navigation
        'OPEN_MARKS_SHEET': [
            r'open\s+(?:the\s+)?marks?\s+(?:sheet\s+)?(?:for\s+|of\s+)?class\s+\d+',
            r'show\s+(?:the\s+)?marks?\s+(?:sheet\s+)?(?:for\s+|of\s+)?class\s+\d+',
            r'go\s+to\s+(?:the\s+)?marks?\s+(?:sheet\s+)?(?:for\s+|of\s+)?class\s+\d+',
            r'display\s+(?:the\s+)?marks?\s+(?:sheet\s+)?(?:for\s+|of\s+)?class\s+\d+',
        ],
        'OPEN_ATTENDANCE_SHEET': [
            r'open\s+(?:the\s+)?attendance\s+(?:sheet\s+)?(?:for\s+|of\s+)?class\s+\d+',
            r'show\s+(?:the\s+)?attendance\s+(?:sheet\s+)?(?:for\s+|of\s+)?class\s+\d+',
            r'go\s+to\s+(?:the\s+)?attendance\s+(?:sheet\s+)?(?:for\s+|of\s+)?class\s+\d+',
            r'display\s+(?:the\s+)?attendance\s+(?:sheet\s+)?(?:for\s+|of\s+)?class\s+\d+',
        ],
        # General navigation (after attendance marking)
        'NAVIGATE_MARKS': [
            r'^open\s+marks?[\s\.,;!?]*$',
            r'^show\s+marks?[\s\.,;!?]*$',
            r'^open\s+(?:the\s+)?marks?\s*(?:page|list)?[\s\.,;!?]*$',
            r'^show\s+(?:the\s+)?marks?\s*(?:page|list)?[\s\.,;!?]*$',
            r'go\s+to\s+(?:the\s+)?marks?\s*(?:page|list)?[\s\.,;!?]*$',
            r'navigate\s+to\s+(?:the\s+)?marks?',
        ],
        'NAVIGATE_ATTENDANCE': [
            r'^open\s+attendance[\s\.,;!?]*$',
            r'^show\s+attendance[\s\.,;!?]*$',
            r'^open\s+(?:the\s+)?attendance\s*(?:page|list)?[\s\.,;!?]*$',
            r'^show\s+(?:the\s+)?attendance\s*(?:page|list)?[\s\.,;!?]*$',
            r'go\s+to\s+(?:the\s+)?attendance\s*(?:page|list)?[\s\.,;!?]*$',
            r'navigate\s+to\s+(?:the\s+)?attendance',
        ],
        # Student details (requires "details" or "info" keywords)
        'VIEW_STUDENT': [
            r'show\s+(?:the\s+)?(?:details|info(?:rmation)?)\s+(?:of|for)\s+(?:student|roll|rule)',
            r'view\s+(?:the\s+)?student\s+(?:details|info)',
            r'student\s+(?:details|info(?:rmation)?)\s+(?:of|for)\s+(?:roll|rule)',
            r'get\s+(?:the\s+)?student\s+(?:details|info(?:rmation)?)',
            r'details\s+(?:of|for)\s+(?:student|roll|rule)',
        ],
    }

    @classmethod
    def normalize_stt_text(cls, text):
        """
        Normalize STT output by converting numeric homophones back to words.

        Whisper often converts:
        - "to"/"too" → 2
        - "for" → 4
        - "one" → 1 (sometimes)
        - Adds random periods: "question 3. as 8." → "question 3 as 8"

        We need to restore these in context.
        """
        text_lower = text.lower().strip()

        logger.info(f"[NORM-0] Original: '{text_lower}'")

        # CRITICAL FIX 1: Convert slash-separated numbers to comma-separated
        # "10/11/12" → "10, 11, 12"
        # "7/9" → "7, 9"
        text_lower = re.sub(
            r'(\d+)/(\d+)',  # Match "digit/digit"
            r'\1, \2',  # Replace with "digit, digit"
            text_lower
        )
        logger.info(f"[NORM-1a] After slash→comma: '{text_lower}'")

        # CRITICAL FIX 2: Convert period-separated number lists to comma-separated
        # "1. 2. 3." → "1, 2, 3"  OR  "7. 19." → "7, 19"
        # This must happen BEFORE removing all periods
        # Apply multiple times to handle overlapping matches (1. 2. 3. → 1, 2, 3)
        prev = None
        while prev != text_lower:
            prev = text_lower
            text_lower = re.sub(
                r'(\d+)\.\s+(\d+)',  # Match "digit. digit"
                r'\1, \2',  # Replace with "digit, digit"
                text_lower
            )
        logger.info(f"[NORM-1b] After period→comma: '{text_lower}'")

        # CRITICAL FIX: Remove remaining periods that break parsing
        # "Update question 3. As 8." → "Update question 3 as 8"
        # But keep decimal points in numbers (4.5)
        text_lower = re.sub(r'\.(?!\d)', ' ', text_lower)  # Remove periods not followed by digit
        text_lower = re.sub(r'\s+', ' ', text_lower).strip()  # Clean up extra spaces
        logger.info(f"[NORM-2] After period removal: '{text_lower}'")

        # FIX: Convert word numbers to digits
        # "question one" → "question 1", "three marks" → "3 marks"
        word_to_num = {
            'zero': '0', 'one': '1', 'two': '2', 'three': '3', 'four': '4',
            'five': '5', 'six': '6', 'seven': '7', 'eight': '8', 'nine': '9',
            'ten': '10', 'eat': '8', 'ate': '8'  # Common mishearings of "eight"
        }

        for word, num in word_to_num.items():
            # Replace word numbers when they appear after "question", "for", or before "marks"
            text_lower = re.sub(rf'\bquestion\s+{word}\b', f'question {num}', text_lower)
            text_lower = re.sub(rf'\bfor\s+{word}\b', f'for {num}', text_lower)  # NEW: "for two" → "for 2"
            text_lower = re.sub(rf'\b{word}\s+marks?\b', f'{num} marks', text_lower)
            text_lower = re.sub(rf'\bas\s+{word}\b', f'as {num}', text_lower)
            text_lower = re.sub(rf'\bto\s+{word}\b', f'to {num}', text_lower)
            text_lower = re.sub(rf'\bgive\s+{word}\b', f'give {num}', text_lower)

        # Special case: "eat as" or "ate as" - remove the word before "as" if it's eat/ate
        # "12345678 eat as 79" → "12345678 as 79"
        text_lower = re.sub(r'\b(eat|ate)\s+as\b', 'as', text_lower)

        logger.info(f"[NORM-3] After word→number: '{text_lower}'")

        # FIX: Common misheard words
        # "months" → "marks", "mugs" → "marks", "box" → "marks", "oceans" → "questions"
        text_lower = re.sub(r'\bmonths?\b', 'marks', text_lower)
        text_lower = re.sub(r'\bmugs?\b', 'marks', text_lower)
        text_lower = re.sub(r'\bbox\b', 'marks', text_lower)
        text_lower = re.sub(r'\boceans?\b', 'questions', text_lower)  # Whisper mishearing
        text_lower = re.sub(r'\bchoose?\b', 'to', text_lower)  # "choose" → "to"
        text_lower = re.sub(r'\bpin\b', 'open', text_lower)  # "pin" → "open"
        text_lower = re.sub(r'\bdate\b', 'update', text_lower)  # "date" → "update"
        text_lower = re.sub(r'\bfor\s+forgive\b', 'for 4', text_lower)  # "for forgive" → "for 4" (Whisper mishearing of "for four")
        text_lower = re.sub(r'\bforgive\b', 'for 4 give', text_lower)  # "forgive" alone → "for 4 give" (less likely but handle it)

        # FIX: Subject-wise command mishearings
        text_lower = re.sub(r'\bit marks off\b', 'enter marks for', text_lower)  # "it marks off" → "enter marks for" (Whisper mishearing)
        text_lower = re.sub(r'\bit marks for\b', 'enter marks for', text_lower)  # "it marks for" → "enter marks for"
        text_lower = re.sub(r'\benter marks off\b', 'enter marks for', text_lower)  # "enter marks off" → "enter marks for"

        # FIX: Time formats (Whisper transcribes numbers as times)
        # "5:00" → "5", "10:30" → "10"
        text_lower = re.sub(r'(\d+):\d+', r'\1', text_lower)

        # FIX: INTELLIGENT split of concatenated question numbers
        # "12345678910" → "1,2,3,4,5,6,7,8,9,10" (preserves 10!)
        # "12345" → "1,2,3,4,5"
        def smart_split_questions(match):
            prefix = match.group(1)  # "questions"
            merged = match.group(2)  # e.g., "12345678910"

            # Check for exact consecutive sequences
            # Must check longer sequences FIRST (most specific)
            if merged == '123456789101112':
                return f"{prefix} 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12"
            elif merged == '1234567891011':
                return f"{prefix} 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11"
            elif merged == '12345678910':
                return f"{prefix} 1, 2, 3, 4, 5, 6, 7, 8, 9, 10"
            elif merged == '123456789':
                return f"{prefix} 1, 2, 3, 4, 5, 6, 7, 8, 9"
            elif merged == '12345678':
                return f"{prefix} 1, 2, 3, 4, 5, 6, 7, 8"
            elif merged == '1234567':
                return f"{prefix} 1, 2, 3, 4, 5, 6, 7"
            elif merged == '123456':
                return f"{prefix} 1, 2, 3, 4, 5, 6"
            elif merged == '12345':
                return f"{prefix} 1, 2, 3, 4, 5"
            elif merged == '1234':
                return f"{prefix} 1, 2, 3, 4"
            elif merged == '123':
                return f"{prefix} 1, 2, 3"

            # Fallback: split all digits
            digits = ', '.join(list(merged))
            return f"{prefix} {digits}"

        # Apply smart splitting for "questions" (plural)
        text_lower = re.sub(
            r'\b(questions)\s+(\d{2,})\b',
            smart_split_questions,
            text_lower
        )

        logger.info(f"[NORM-4] After smart question splitting: '{text_lower}'")

        # FIX: INTELLIGENT split of marks after "as"
        # "as 7 12 911 11 5" → "as 7, 1, 2, 9, 1, 1, 1, 1, 5"
        # Strategy: Preserve ONLY "10" as it's most common max score; split all others
        def smart_split_marks(full_text):
            # Extract the part after "as"
            match = re.search(r'\bas\s+([\d\s,/]+)', full_text)
            if not match:
                return full_text

            marks_part = match.group(1).strip()
            # Get all numbers (split by space, comma, or slash)
            numbers = re.findall(r'\d+(?:\.\d+)?', marks_part)  # Support decimals

            split_numbers = []
            for num in numbers:
                # Skip if it's a decimal (4.5, 5.5, etc.)
                if '.' in num:
                    split_numbers.append(num)
                elif len(num) == 1:
                    # Single digit - keep as is
                    split_numbers.append(num)
                elif num == '10':
                    # Preserve 10 (most common max score)
                    split_numbers.append(num)
                else:
                    # Everything else: split into individual digits
                    # 11 → 1,1
                    # 12 → 1,2
                    # 911 → 9,1,1
                    split_numbers.extend(list(num))

            # Reconstruct the text
            new_marks = ', '.join(split_numbers)
            return re.sub(r'\bas\s+[\d\s,/]+', f'as {new_marks}', full_text, count=1)

        text_lower = smart_split_marks(text_lower)
        logger.info(f"[NORM-5] After smart marks splitting: '{text_lower}'")

        # FIX: Support range syntax "questions 1 to 10"
        # "questions 1 to 10" → "questions 1, 2, 3, 4, 5, 6, 7, 8, 9, 10"
        def expand_range(match):
            prefix = match.group(1)  # "questions"
            start = int(match.group(2))
            end = int(match.group(3))
            # Generate range
            if start <= end and end - start < 20:  # Sanity check
                numbers = ', '.join(str(i) for i in range(start, end + 1))
                return f"{prefix} {numbers}"
            return match.group(0)  # Return unchanged if invalid

        # CRITICAL FIX: Only expand ranges when NOT followed by a decimal point
        # "question 5 to 7.5" should NOT expand (7.5 is a score, not a range end)
        text_lower = re.sub(
            r'\b(questions?)\s+(\d+)\s*(?:to|through|-)\s*(\d+)(?!\.)\b',  # Negative lookahead for decimal
            expand_range,
            text_lower
        )
        logger.info(f"[NORM-6] After range expansion: '{text_lower}'")

        # Pattern 1: "update marks 4 questions" → "update marks for questions"
        # Look for: verb + "4" + noun (where 4 likely means "for")
        text_lower = re.sub(
            r'\b(update|change|set|enter)\s+marks?\s+4\s+(questions?|roll|rule)',
            r'\1 marks for \2',
            text_lower
        )

        # Pattern 2: "2 questions" → "to questions" (less common, be careful)
        # Only if "2" appears right before "question" without other context
        # Actually, this is risky - skip for now

        # Pattern 3: "question 1 2 3" → "question 1, 2, 3" (add commas for clarity)
        # This helps with parsing parallel lists
        text_lower = re.sub(
            r'question[s]?\s+(\d+)\s+(\d+)\s+(\d+)',
            r'questions \1, \2, \3',
            text_lower
        )

        # Pattern 4: "as 4 5 6" → "as 4, 5, 6" (add commas)
        text_lower = re.sub(
            r'as\s+(\d+)\s+(\d+)\s+(\d+)',
            r'as \1, \2, \3',
            text_lower
        )

        # Pattern 5: More aggressive comma insertion for number sequences
        # "1 2 3 4" → "1, 2, 3, 4" but only after keywords
        # First, handle space-separated numbers (without existing commas)
        text_lower = re.sub(
            r'(questions?|as|give)\s+((?:\d+\s+)+\d+)(?!\d)',  # Match keyword followed by space-separated numbers
            lambda m: m.group(1) + ' ' + ', '.join(re.findall(r'\d+', m.group(2))),
            text_lower
        )

        # Cleanup: Remove duplicate commas and extra spaces
        text_lower = re.sub(r',\s*,+', ',', text_lower)  # ",," → ","
        text_lower = re.sub(r'\s+', ' ', text_lower).strip()  # Multiple spaces → single space

        logger.info(f"Normalized text: '{text_lower}'")
        return text_lower

    @classmethod
    def extract_intent(cls, text):
        """
        Extract intent from text.

        Args:
            text (str): Transcribed text

        Returns:
            str: Intent type (ENTER_MARKS, MARK_ATTENDANCE, VIEW_STUDENT, or UNKNOWN)
        """
        # First normalize the text to handle STT quirks
        text_normalized = cls.normalize_stt_text(text)
        text_lower = text_normalized.lower()

        for intent, patterns in cls.INTENT_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    logger.info(f"Intent detected: {intent} using pattern: {pattern}")
                    return intent

        logger.warning(f"No intent matched for text: {text}")
        return 'UNKNOWN'


class EntityExtractor:
    """
    Extracts entities from transcribed text based on intent.
    """

    @classmethod
    def extract_entities(cls, text, intent, context=None):
        """
        Extract entities based on intent.

        Args:
            text (str): Transcribed text
            intent (str): Detected intent
            context (dict): Optional context (e.g., current class/section from page)

        Returns:
            dict: Extracted entities
        """
        if context is None:
            context = {}

        # Normalize text before entity extraction (same as intent extraction)
        text = IntentExtractor.normalize_stt_text(text)

        if intent == 'BATCH_UPDATE_QUESTION_MARKS':
            return cls._extract_batch_question_marks_entities(text, context)
        elif intent == 'UPDATE_QUESTION_MARKS':
            return cls._extract_question_marks_entities(text, context)
        elif intent == 'OPEN_QUESTION_SHEET':
            return cls._extract_question_sheet_navigation(text, context)
        elif intent == 'ENTER_MARKS' or intent == 'UPDATE_MARKS':
            return cls._extract_marks_entities(text, context)
        elif intent == 'MARK_ATTENDANCE':
            return cls._extract_attendance_entities(text, context)
        elif intent == 'VIEW_STUDENT':
            return cls._extract_student_view_entities(text, context)
        elif intent == 'OPEN_MARKS_SHEET' or intent == 'OPEN_ATTENDANCE_SHEET':
            return cls._extract_class_section(text, context)
        elif intent == 'NAVIGATE_MARKS' or intent == 'NAVIGATE_ATTENDANCE':
            return {}  # No entities needed for simple navigation
        else:
            return {}

    @classmethod
    def _extract_marks_entities(cls, text, context=None):
        """
        Extract entities for marks entry.

        Expected format examples:
        - "Enter marks for roll number 22, class 9B. Maths 85, Hindi 78, English 92"
        - "Add marks for roll no 5, class 10A. Science 90"
        - "Update marks for roll 1 maths 95" (when context provided)
        """
        if context is None:
            context = {}

        logger.info(f"Extracting marks entities from text: '{text}'")
        logger.info(f"Context: {context}")

        entities = {}

        # Extract roll number (handle "rule" as speech recognition error for "roll", allow periods)
        roll_patterns = [
            r'(?:roll|rule)[\.\s]+(?:number|no\.?|num|#)?[\.\s]*(\d+)',
            r'(?:roll|rule)[\.\s]+(\d+)',
        ]
        for pattern in roll_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                entities['roll_number'] = int(match.group(1))
                break

        # Extract class (grade number) - use context as fallback
        class_patterns = [
            r'class\s+(\d+)',
            r'grade\s+(\d+)',
        ]
        for pattern in class_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                entities['class'] = int(match.group(1))
                break

        # Extract section
        section_patterns = [
            r'class\s+\d+\s*([A-Za-z])',
            r'section\s+([A-Za-z])',
        ]
        for pattern in section_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                entities['section'] = match.group(1).upper()
                break

        # Use context as fallback if class/section not found in text
        if 'class' not in entities and 'class' in context:
            entities['class'] = context['class']
            logger.info(f"Using class from context: {context['class']}")

        if 'section' not in entities and 'section' in context:
            entities['section'] = context['section']
            logger.info(f"Using section from context: {context['section']}")

        # Extract marks for subjects
        entities['marks'] = cls._extract_subject_marks(text)

        logger.info(f"Extracted marks entities: {entities}")
        return entities

    @classmethod
    def _extract_question_marks_entities(cls, text, context=None):
        """
        Extract entities for question-wise marks update.

        Expected format examples:
        - "Update Maths question 3 for roll number 1 to 1.5 marks"
        - "Set Science question 5 for roll 10 to 8 marks"
        - "Change English question 2 for roll 5 to 7.5"
        """
        if context is None:
            context = {}

        logger.info(f"Extracting question marks entities from text: '{text}'")
        logger.info(f"Context: {context}")

        entities = {}

        # Extract roll number
        roll_patterns = [
            r'(?:for\s+|of\s+)?(?:roll|rule)[\.\s]+(?:number|no\.?|num|#)?[\.\s]*(\d+)',
            r'(?:roll|rule)[\.\s]+(\d+)',
        ]
        for pattern in roll_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                entities['roll_number'] = int(match.group(1))
                break

        # Extract question number
        question_patterns = [
            r'question\s+(?:number\s+|no\.?\s+|#)?(\d+)',
            r'q\s*(?:number\s+|no\.?\s+|#)?(\d+)',
        ]
        for pattern in question_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                entities['question_number'] = int(match.group(1))
                break

        # Extract subject
        subject_keywords = {
            'mathematics': 'MATH',
            'maths': 'MATH',
            'math': 'MATH',
            'hindi': 'HINDI',
            'english': 'ENGLISH',
            'science': 'SCIENCE',
            'social studies': 'SOCIAL',
            'social': 'SOCIAL',
            'computer': 'COMPUTER',
            'computer science': 'COMPUTER',
        }

        for keyword, code in subject_keywords.items():
            if re.search(r'\b' + keyword + r'\b', text, re.IGNORECASE):
                entities['subject_code'] = code
                break

        # Extract marks value
        marks_patterns = [
            r'(?:to|give|set|put|mark|as|with)\s+(\d+(?:\.\d+)?)\s*(?:marks?|points?)?',
            r'(\d+(?:\.\d+)?)\s+(?:marks?|points?)',
        ]
        for pattern in marks_patterns:
            # Find all matches and get the last one (usually the marks value)
            matches = list(re.finditer(pattern, text, re.IGNORECASE))
            if matches:
                last_match = matches[-1]
                value = float(last_match.group(1))

                # Check if this value looks like marks (not roll/question number)
                # Context: "question 3 to 8 marks" - 8 is marks, 3 is question
                # If value appears after "to/as/with", it's likely marks
                context_before = text[:last_match.start()].lower()
                if re.search(r'(?:to|as|with|at|give|set|put)\s*$', context_before):
                    entities['marks_obtained'] = value
                    break
                # If no question/roll number found yet and value is small, it could be marks
                elif 'question_number' in entities and value <= 100:
                    entities['marks_obtained'] = value
                    break

        # Use context for class/section
        if 'class' in context:
            entities['class'] = context['class']
            logger.info(f"Using class from context: {context['class']}")

        if 'section' in context:
            entities['section'] = context['section']
            logger.info(f"Using section from context: {context['section']}")

        # Use context for roll_number if not found in text
        if 'roll_number' not in entities and 'roll_number' in context:
            entities['roll_number'] = int(context['roll_number'])
            logger.info(f"Using roll_number from context: {context['roll_number']}")

        # Use context for subject_id if not found in text
        # Map subject_id to subject_code
        if 'subject_code' not in entities and 'subject_id' in context:
            subject_id_mapping = {
                '1': 'MATH',
                '2': 'HINDI',
                '3': 'ENGLISH',
                '4': 'SCIENCE',
                '5': 'SOCIAL',
            }
            subject_code = subject_id_mapping.get(str(context['subject_id']))
            if subject_code:
                entities['subject_code'] = subject_code
                logger.info(f"Using subject_code from context subject_id: {context['subject_id']} -> {subject_code}")

        logger.info(f"Extracted question marks entities: {entities}")
        return entities

    @classmethod
    def _extract_batch_question_marks_entities(cls, text, context=None):
        """
        Extract entities for batch question marks update.

        Expected format examples:
        - "Update marks for question 1 marks 3, 2 marks 5, 3 marks 6, 7 marks 8"
        - "For 1 give 3, for 4 give 6, for 7 give 8 marks"
        - "Question 1 is 3, question 2 is 5, question 5 is 9"
        - "Questions 1, 2, 3 as 4, 5, 6" (PARALLEL LISTS - NEW!)
        """
        if context is None:
            context = {}

        logger.info(f"Extracting BATCH question marks entities from text: '{text}'")
        logger.info(f"Context: {context}")

        entities = {}
        updates = []

        # STRATEGY 1: Try parallel list parsing first (most explicit)
        # Pattern: "questions 1, 2, 3 as 4, 5, 6" - MUST have comma (indicates multiple questions)
        # CRITICAL: Require comma to avoid matching single pairs like "question 1 give 5"
        parallel_pattern = r'questions?\s+([\d,\s]+,[\d,\s]+)\s+(?:as|marks?|give)\s+([\d,\s]+)'
        parallel_match = re.search(parallel_pattern, text, re.IGNORECASE)

        import sys
        print(f"\n[DEBUG] STRATEGY 1: Testing parallel pattern on text: '{text}'", flush=True)
        print(f"[DEBUG] Parallel match found: {bool(parallel_match)}", flush=True)
        sys.stdout.flush()

        if parallel_match:
            print(f"[DEBUG] Parallel match groups: group1='{parallel_match.group(1)}', group2='{parallel_match.group(2)}'", flush=True)
            sys.stdout.flush()
            logger.info("Detected PARALLEL LIST pattern")
            question_str = parallel_match.group(1)
            marks_str = parallel_match.group(2)

            logger.info(f"Question string extracted: '{question_str}'")
            logger.info(f"Marks string extracted: '{marks_str}'")

            # Extract numbers from each side
            question_nums = [int(x.strip()) for x in re.findall(r'\d+', question_str)]
            marks_nums = [float(x.strip()) for x in re.findall(r'\d+(?:\.\d+)?', marks_str)]

            logger.info(f"Questions parsed: {question_nums} (count: {len(question_nums)})")
            logger.info(f"Marks parsed: {marks_nums} (count: {len(marks_nums)})")

            # Validate list lengths match
            if len(question_nums) == len(marks_nums):
                for q_num, mark in zip(question_nums, marks_nums):
                    updates.append({
                        'question_number': q_num,
                        'marks_obtained': mark
                    })
                logger.info(f"Parallel list parsing: {len(updates)} updates created")
            else:
                logger.warning(f"Parallel lists length mismatch: {len(question_nums)} questions vs {len(marks_nums)} marks")

        # STRATEGY 2: Fallback to pair-wise patterns if parallel list didn't work
        if not updates:
            import sys
            print(f"\n[DEBUG] STRATEGY 2: Trying pair-wise patterns on text: '{text}'", flush=True)
            sys.stdout.flush()
            logger.info(f"[DEBUG] STRATEGY 2: Trying pair-wise patterns on text: '{text}'")
            # Pattern variations for question-marks pairs
            # 1. "question 1 marks 3" or "1 marks 3" - ALLOW COMMAS
            pattern1 = r'(?:question\s+)?(\d+)[\s,]+(?:marks?|is|give)\s+(\d+(?:\.\d+)?)'
            # 2. "for 1, give 3" or "for question 1, give 3" - ALLOW COMMAS
            pattern2 = r'(?:for\s+)?(?:question\s+)?(\d+)[\s,]+give\s+(\d+(?:\.\d+)?)'
            # 3. "question 1 is 3"
            pattern3 = r'question\s+(\d+)\s+is\s+(\d+(?:\.\d+)?)'
            # 4. "1 -> 3" or "1: 3" (shorthand)
            pattern4 = r'(\d+)\s*(?:->|:|to)\s*(\d+(?:\.\d+)?)'

            # Combine all patterns
            all_patterns = [pattern1, pattern2, pattern3, pattern4]

            # Try each pattern
            for pattern in all_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                print(f"[DEBUG] Pattern '{pattern}' found {len(matches)} raw matches: {matches}", flush=True)
                sys.stdout.flush()
                logger.info(f"[DEBUG] Pattern '{pattern}' found {len(matches)} raw matches: {matches}")
                if matches:
                    for match in matches:
                        question_num = int(match[0])
                        marks = float(match[1])
                        print(f"[DEBUG] Processing match: Q{question_num} = {marks}", flush=True)
                        sys.stdout.flush()
                        logger.info(f"[DEBUG] Processing match: Q{question_num} = {marks}")

                        # Avoid duplicates
                        if not any(u['question_number'] == question_num for u in updates):
                            updates.append({
                                'question_number': question_num,
                                'marks_obtained': marks
                            })
                            print(f"[DEBUG] Added Q{question_num} = {marks} to updates (total: {len(updates)})", flush=True)
                            sys.stdout.flush()
                            logger.info(f"[DEBUG] Added Q{question_num} = {marks} to updates (total: {len(updates)})")
                        else:
                            print(f"[DEBUG] Skipped duplicate Q{question_num}", flush=True)
                            sys.stdout.flush()
                            logger.info(f"[DEBUG] Skipped duplicate Q{question_num}")
                    print(f"[DEBUG] Pattern '{pattern}' processed {len(matches)} matches, updates now: {len(updates)}", flush=True)
                    sys.stdout.flush()
                    logger.info(f"Pattern '{pattern}' processed {len(matches)} matches, updates now: {len(updates)}")

        # STRATEGY 3: Fallback for raw number lists without "as" keyword
        # "questions 1, 2, 3, 4, 5, 6, 7, 8, 9, 10" (just numbers, no marks)
        if not updates:
            logger.info("Trying STRATEGY 3: Raw number list without separator")
            # Look for "questions" followed by many numbers
            raw_pattern = r'questions?\s+([\d,\s]+?)(?:\.|$|until|till|to\b)'
            raw_match = re.search(raw_pattern, text, re.IGNORECASE)

            if raw_match:
                numbers_str = raw_match.group(1)
                all_numbers = [int(x.strip()) for x in re.findall(r'\d+', numbers_str)]
                logger.info(f"Extracted {len(all_numbers)} numbers: {all_numbers}")

                # If even count, try splitting in half (first half = questions, second half = marks)
                if len(all_numbers) >= 4 and len(all_numbers) % 2 == 0:
                    mid = len(all_numbers) // 2
                    question_nums = all_numbers[:mid]
                    marks_nums = all_numbers[mid:]

                    logger.info(f"Split into questions: {question_nums}, marks: {marks_nums}")

                    for q_num, mark in zip(question_nums, marks_nums):
                        updates.append({
                            'question_number': q_num,
                            'marks_obtained': float(mark)
                        })
                    logger.info(f"Raw list parsing: {len(updates)} updates created")
                else:
                    logger.warning(f"Cannot split {len(all_numbers)} numbers - need even count for question-marks pairs")

        # If we found multiple updates, this is a batch operation
        if len(updates) < 2:
            # Not a batch - might be misclassified, log warning
            logger.warning(f"BATCH intent detected but only {len(updates)} updates found")

        # Sort by question number
        updates.sort(key=lambda x: x['question_number'])

        entities['updates'] = updates

        # Use context for class/section/roll/subject
        if 'class' in context:
            entities['class'] = context['class']
        if 'section' in context:
            entities['section'] = context['section']
        if 'roll_number' in context:
            entities['roll_number'] = int(context['roll_number'])
        if 'subject_id' in context:
            # Map subject_id to subject_code
            subject_id_mapping = {
                '1': 'MATH',
                '2': 'HINDI',
                '3': 'ENGLISH',
                '4': 'SCIENCE',
                '5': 'SOCIAL',
            }
            subject_code = subject_id_mapping.get(str(context['subject_id']))
            if subject_code:
                entities['subject_code'] = subject_code

        logger.info(f"Extracted BATCH question marks entities: {entities}")
        return entities

    @classmethod
    def _extract_subject_marks(cls, text):
        """
        Extract subject-marks pairs from text.

        Examples:
        - "Maths 85, Hindi 78, English 92"
        - "Math 85 Hindi 78"
        - "Mathematics: 85, Science: 90"
        """
        marks_dict = {}

        # Subject name mappings (handles variations including common speech recognition errors)
        subject_mappings = {
            'math': 'MATH',
            'maths': 'MATH',
            'mathematics': 'MATH',
            'match': 'MATH',  # Common speech recognition error
            'mass': 'MATH',   # Common speech recognition error
            'hindi': 'HINDI',
            'english': 'ENGLISH',
            'science': 'SCIENCE',
            'social': 'SOCIAL',
            'social studies': 'SOCIAL',
            'computer': 'COMPUTER',
            'cs': 'COMPUTER',
            'physical education': 'PE',
            'pe': 'PE',
        }

        # Pattern: Subject name followed by marks (allow periods between words)
        # Supports: "Math 85", "Maths: 85", "Match. 24", "match 91"
        pattern = r'([a-zA-Z\s\.]+?)[\s:\.\-]+(\d+)'

        matches = re.finditer(pattern, text)

        logger.info(f"Found {len(list(re.finditer(pattern, text)))} potential subject-marks matches")

        for match in matches:
            # Strip periods and whitespace from subject text
            subject_text = match.group(1).strip().replace('.', '').strip().lower()
            marks_value = int(match.group(2))

            logger.info(f"Checking match: subject='{subject_text}', marks={marks_value}")

            # Skip if the subject_text itself is ONLY a keyword (roll, rule, class, etc)
            # But allow if it contains valid subject names
            if subject_text in ['roll', 'rule', 'class', 'grade', 'number', 'section', 'update', 'marks', 'for', 'of']:
                logger.info(f"  Skipping - subject text is keyword: '{subject_text}'")
                continue

            # Skip ONLY if "roll/rule/#" appears IMMEDIATELY before the subject (within 10 chars)
            # This prevents "roll 1" from being matched as marks, but allows "for roll 1 maths 22"
            context_immediate = text[max(0, match.start() - 10):match.start()].lower()

            # Check if this looks like "roll <number>" pattern
            if re.search(r'(roll|rule|#)\s*$', context_immediate):
                logger.info(f"  Skipping - looks like roll number pattern")
                continue

            # Map to standard subject code
            matched = False
            for key, code in subject_mappings.items():
                if key in subject_text:
                    marks_dict[code.lower()] = marks_value
                    logger.info(f"  Matched! {key} -> {code}: {marks_value}")
                    matched = True
                    break

            if not matched:
                logger.info(f"  No subject mapping found for '{subject_text}'")

        logger.info(f"Extracted subject marks: {marks_dict}")
        return marks_dict

    @classmethod
    def _extract_attendance_entities(cls, text, context=None):
        """
        Extract entities for attendance marking.

        Expected format:
        - "Mark attendance for class 9B"
        - "Mark everyone present in class 10A"
        - "Take attendance of 9th B"
        - "Mark all present" (when context provided)
        """
        if context is None:
            context = {}

        entities = {}

        # Extract class (grade number)
        class_patterns = [
            r'class\s+(\d+)',
            r'grade\s+(\d+)',
            r'(\d+)(?:th|st|nd|rd)',
        ]
        for pattern in class_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                entities['class'] = int(match.group(1))
                break

        # Extract section
        section_patterns = [
            r'class\s+\d+\s*([A-Za-z])',
            r'section\s+([A-Za-z])',
            r'\d+(?:th|st|nd|rd)?\s*([A-Za-z])\b',
        ]
        for pattern in section_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                entities['section'] = match.group(1).upper()
                break

        # Use context as fallback if class/section not found in text
        if 'class' not in entities and 'class' in context:
            entities['class'] = context['class']
            logger.info(f"Using class from context: {context['class']}")

        if 'section' not in entities and 'section' in context:
            entities['section'] = context['section']
            logger.info(f"Using section from context: {context['section']}")

        # Check if marking everyone or individual student
        # Match: "all", "everyone", "all students", "whole class", "mark all present/absent"
        if re.search(r'\b(everyone|all\s+(?:students?|present|absent)?|whole\s+class)\b', text, re.IGNORECASE):
            entities['mark_all'] = True
        else:
            entities['mark_all'] = False

            # Check for individual roll number
            roll_patterns = [
                r'(?:roll|rule)[\.\s]+(?:number|no\.?|num|#)?[\.\s]*(\d+)',
                r'(?:roll|rule)[\.\s]+(\d+)',
            ]
            for pattern in roll_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    entities['roll_number'] = int(match.group(1))
                    break

        # Determine status (PRESENT or ABSENT)
        if re.search(r'\b(absent|leave)\b', text, re.IGNORECASE):
            entities['status'] = 'ABSENT'
        elif re.search(r'\bpresent\b', text, re.IGNORECASE):
            entities['status'] = 'PRESENT'
        else:
            # Default to PRESENT if not specified
            entities['status'] = 'PRESENT'

        # Extract excluded roll numbers (e.g., "except roll 2, 3" or "except roll number 2 and 3")
        except_match = re.search(r'except\s+(?:roll|role)?\s*(?:number|no\.?|num)?\s*([\d\s,and]+)', text, re.IGNORECASE)
        if except_match:
            # Extract all numbers from the except clause
            excluded_rolls_text = except_match.group(1)
            excluded_rolls = re.findall(r'\d+', excluded_rolls_text)
            entities['excluded_rolls'] = [int(roll) for roll in excluded_rolls]
            logger.info(f"Excluding roll numbers: {entities['excluded_rolls']}")

        logger.info(f"Extracted attendance entities: {entities}")
        return entities

    @classmethod
    def _extract_student_view_entities(cls, text, context=None):
        """
        Extract entities for viewing student details.

        Expected format:
        - "Show details of student roll number 22, class 9B"
        - "View student roll no 5 class 10A"
        """
        if context is None:
            context = {}

        entities = {}

        # Extract roll number (handle "rule" as speech recognition error for "roll", allow periods)
        roll_patterns = [
            r'(?:roll|rule)[\.\s]+(?:number|no\.?|num|#)?[\.\s]*(\d+)',
            r'(?:roll|rule)[\.\s]+(\d+)',
        ]
        for pattern in roll_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                entities['roll_number'] = int(match.group(1))
                break

        # Extract class
        class_patterns = [
            r'class\s+(\d+)',
            r'grade\s+(\d+)',
        ]
        for pattern in class_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                entities['class'] = int(match.group(1))
                break

        # Extract section
        section_patterns = [
            r'class\s+\d+\s*([A-Za-z])',
            r'section\s+([A-Za-z])',
        ]
        for pattern in section_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                entities['section'] = match.group(1).upper()
                break

        # Use context as fallback if class/section not found in text
        if 'class' not in entities and 'class' in context:
            entities['class'] = context['class']

        if 'section' not in entities and 'section' in context:
            entities['section'] = context['section']

        logger.info(f"Extracted student view entities: {entities}")
        return entities

    @classmethod
    def _extract_class_section(cls, text, context=None):
        """
        Extract class and section for navigation commands.

        Expected format:
        - "Open marks for class 8B"
        - "Show attendance for class 10A"
        - "Go to marks sheet class 9 section C"
        """
        if context is None:
            context = {}

        entities = {}

        # Extract class (grade number)
        class_patterns = [
            r'class\s+(\d+)',
            r'grade\s+(\d+)',
        ]
        for pattern in class_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                entities['class'] = int(match.group(1))
                break

        # Extract section
        section_patterns = [
            r'class\s+\d+\s*([A-Za-z])',
            r'section\s+([A-Za-z])',
        ]
        for pattern in section_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                entities['section'] = match.group(1).upper()
                break

        # Context is not typically used for navigation commands since they
        # should explicitly specify the target class. But keeping the parameter
        # for consistency.

        logger.info(f"Extracted class/section entities: {entities}")
        return entities

    @classmethod
    def _extract_question_sheet_navigation(cls, text, context=None):
        """
        Extract entities for navigating to question-wise page.

        Expected format:
        - "Open question-wise marksheet for roll 14 maths"
        - "Show questionwise marks for roll number 5 english"
        """
        if context is None:
            context = {}

        entities = {}

        # Extract roll number
        roll_patterns = [
            r'(?:roll|rule)\s+(?:number\s+|no\.?\s+|#)?(\d+)',
        ]
        for pattern in roll_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                entities['roll_number'] = int(match.group(1))
                break

        # Extract subject
        subject_keywords = {
            'mathematics': 'MATH',
            'maths': 'MATH',
            'math': 'MATH',
            'hindi': 'HINDI',
            'english': 'ENGLISH',
            'science': 'SCIENCE',
            'social studies': 'SOCIAL',
            'social': 'SOCIAL',
            'computer': 'COMPUTER',
        }

        for keyword, code in subject_keywords.items():
            if re.search(r'\b' + keyword + r'\b', text, re.IGNORECASE):
                entities['subject_code'] = code
                break

        # Use context for class/section
        if 'class' in context:
            entities['class'] = context['class']

        if 'section' in context:
            entities['section'] = context['section']

        logger.info(f"Extracted question sheet navigation entities: {entities}")
        return entities
