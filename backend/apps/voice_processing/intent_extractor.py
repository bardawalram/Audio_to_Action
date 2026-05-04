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
        # Cancel/Stop/Undo commands (MUST be first - immediate action)
        'CANCEL': [
            r'^cancel[\s\.,;!?]*$',
            r'^cancel\s+(?:that|this|it|command)[\s\.,;!?]*$',
            r'^stop[\s\.,;!?]*$',
            r'^stop\s+(?:that|this|it|command)[\s\.,;!?]*$',
            r'^undo[\s\.,;!?]*$',
            r'^undo\s+(?:that|this|it|last)[\s\.,;!?]*$',
            r'^never\s*mind[\s\.,;!?]*$',
            r'^forget\s+(?:it|that|this)[\s\.,;!?]*$',
            r'^abort[\s\.,;!?]*$',
            r'^go\s+back[\s\.,;!?]*$',
            r'^close[\s\.,;!?]*$',
            r'^dismiss[\s\.,;!?]*$',
            # Hindi
            r'^ruko[\s\.,;!?]*$',  # "stop" in Hindi
            r'^band\s+karo[\s\.,;!?]*$',  # "close/stop" in Hindi
            r'^nahi[\s\.,;!?]*$',  # "no" in Hindi
            r'^mat\s+karo[\s\.,;!?]*$',  # "don't do" in Hindi
        ],
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
            r'mark\s+(?:all|everyone)\s+(?:as\s+)?absent\s+except',
            r'mark\s+class\s+\d+\s*[a-z]?\s+(?:as\s+)?present',
            # Individual student: "mark absent for student 3", "mark student 3 absent"
            r'mark\s+(?:as\s+)?(?:absent|present)\s+(?:for\s+)?(?:student|roll|rule)\s+\d+',
            r'mark\s+(?:student|roll|rule)\s+\d+\s+(?:as\s+)?(?:absent|present)',
            r'mark\s+(?:student|roll|rule)\s+(?:number\s+)?\d+\s+(?:as\s+)?(?:absent|present)',
            # Short forms without "mark" prefix (when on attendance page)
            r'^(?:all|everyone)\s+(?:as\s+)?present[\s\.,;!?]*$',
            r'^(?:all|everyone)\s+(?:as\s+)?absent[\s\.,;!?]*$',
            r'^(?:all|everyone)\s+present\s+except',
            r'^(?:all|everyone)\s+absent\s+except',
            r'^all\s+present\s+except\s+(?:roll|student|rule)',
            r'^all\s+absent\s+except\s+(?:roll|student|rule)',
            # Individual student short forms: "student 3 absent", "roll 5 present"
            r'^(?:student|roll|rule)\s+\d+\s+(?:as\s+)?(?:absent|present)[\s\.,;!?]*$',
            r'^(?:absent|present)\s+(?:for\s+)?(?:student|roll|rule)\s+\d+[\s\.,;!?]*$',
        ],
        # Batch update marks for MULTIPLE students (MUST be before UPDATE_MARKS)
        'BATCH_UPDATE_MARKS': [
            # "update marks for student 3 ... update marks for student 4 ..."
            r'(?:update|enter|add|set|change)[\.\s]+(?:the\s+)?marks?.*(?:student|roll|rule)[\.\s]+\d+.*(?:update|enter|add|set|change)[\.\s]+(?:the\s+)?marks?.*(?:student|roll|rule)[\.\s]+\d+',
            # "student 3 maths 90 ... student 4 maths 80 ..."
            r'(?:student|roll|rule)[\.\s]+\d+\s+(?:maths?|mathematics|hindi|english|science|social|computer)\s+\d+.*(?:student|roll|rule)[\.\s]+\d+\s+(?:maths?|mathematics|hindi|english|science|social|computer)\s+\d+',
        ],
        # Update marks (before ENTER_MARKS and navigation)
        'UPDATE_MARKS': [
            # Patterns with student/roll/rule
            r'update[\.\s]+(?:the\s+)?marks?[\.\s]+(?:for\s+|of\s+|to\s+)?(?:student|roll|rule)[\.\s]+(?:number\s+|no\.?\s+|#|to\s+)?(\d+)',
            r'update[\.\s]+(?:the\s+)?marks?[\.\s]+(?:student|roll|rule)[\.\s]+(?:to|for|number)?\s*(\d+)',
            r'change[\.\s]+(?:the\s+)?marks?[\.\s]+(?:for\s+|of\s+|to\s+)?(?:student|roll|rule)[\.\s]+(?:number\s+|no\.?\s+|#)?(\d+)',
            r'modify[\.\s]+(?:the\s+)?marks?[\.\s]+(?:for\s+|of\s+)?(?:student|roll|rule)[\.\s]+(?:number\s+|no\.?\s+|#)?(\d+)',
            r'set[\.\s]+(?:the\s+)?marks?[\.\s]+(?:for\s+|of\s+)?(?:student|roll|rule)[\.\s]+(?:number\s+|no\.?\s+|#)?(\d+)',
            # Subject-wise patterns: "update marks for student 1 maths 90 hindi 80"
            r'update[\.\s]+(?:the\s+)?marks?[\.\s]+(?:for\s+)?(?:student|roll|rule)[\.\s]+(?:number\s+)?(\d+)[\.\s]+(?:maths?|mathematics|hindi|english|science|social|computer)',
            # SHORT FORMS: "roll 1 maths 90 hindi 85" or "student 1 maths 90"
            r'^(?:roll|student|rule)\s+(?:number\s+)?(\d+)\s+(?:maths?|mathematics|hindi|english|science|social|computer)\s+\d+',
            # Even shorter: just roll number + subjects when on marks page
            r'^(\d+)\s+(?:maths?|mathematics|hindi|english|science|social|computer)\s+\d+',
        ],
        # Marks entry (before navigation)
        'ENTER_MARKS': [
            r'enter\s+(?:the\s+)?marks?\s+for\s+(?:student|roll|rule)',
            r'add\s+(?:the\s+)?marks?\s+for\s+(?:student|roll|rule)',
            r'put\s+(?:the\s+)?marks?\s+for\s+(?:student|roll|rule)',
            r'give\s+(?:the\s+)?marks?\s+for\s+(?:student|roll|rule)',
            r'submit\s+(?:the\s+)?marks?\s+for\s+(?:student|roll|rule)',
        ],
        # Open question-wise marksheet (MUST be before OPEN_MARKS_SHEET)
        'OPEN_QUESTION_SHEET': [
            r'open\s+(?:the\s+)?question[\s-]?wise\s+(?:marks?|marksheet)\s+(?:for\s+|of\s+)?(?:roll|rule)\s+(?:number\s+|no\.?\s+|#)?(\d+)\s+(?:maths?|mathematics|hindi|english|science|social|computer)',
            r'show\s+(?:the\s+)?question[\s-]?wise\s+(?:marks?|marksheet)\s+(?:for\s+|of\s+)?(?:roll|rule)\s+(?:number\s+|no\.?\s+|#)?(\d+)\s+(?:maths?|mathematics|hindi|english|science|social|computer)',
            r'go\s+to\s+(?:the\s+)?question[\s-]?wise\s+(?:marks?|marksheet|page)\s+(?:for\s+|of\s+)?(?:roll|rule)\s+(?:number\s+|no\.?\s+|#)?(\d+)\s+(?:maths?|mathematics|hindi|english|science|social|computer)',
        ],
        # SELECT SECTION: Class specified but section NOT specified (MUST be before OPEN_MARKS_SHEET)
        # Matches: "open first year", "open 1st", "open class 1", "open 1st year"
        'SELECT_SECTION': [
            # "open first year" or "open first" (word form)
            r'^open\s+(?:the\s+)?first(?:\s+year)?[\s\.,;!?]*$',
            r'^open\s+(?:the\s+)?second(?:\s+year)?[\s\.,;!?]*$',
            r'^open\s+(?:the\s+)?third(?:\s+year)?[\s\.,;!?]*$',
            # "open 1st year" or "open 1st" (ordinal without section letter)
            r'^open\s+(?:the\s+)?(\d+)(?:st|nd|rd|th)(?:\s+year)?[\s\.,;!?]*$',
            # "open class 1" or "open class 1 marks" (no section letter)
            r'^open\s+(?:the\s+)?class\s+(\d+)(?:\s+marks?)?[\s\.,;!?]*$',
            # "go to 1st" or "go to class 1" (no section letter)
            r'^go\s+to\s+(?:the\s+)?(\d+)(?:st|nd|rd|th)(?:\s+year)?[\s\.,;!?]*$',
            r'^go\s+to\s+(?:the\s+)?class\s+(\d+)(?:\s+marks?)?[\s\.,;!?]*$',
            # "show 1st year" or "show class 1"
            r'^show\s+(?:the\s+)?(\d+)(?:st|nd|rd|th)(?:\s+year)?[\s\.,;!?]*$',
            r'^show\s+(?:the\s+)?class\s+(\d+)(?:\s+marks?)?[\s\.,;!?]*$',
        ],
        # Specific class navigation
        'OPEN_MARKS_SHEET': [
            # Standard: "open marks for class 1A" or "open marks for class 1 A"
            r'open\s+(?:the\s+)?marks?\s+(?:sheet\s+)?(?:for\s+|of\s+)?class\s+\d+\s*[a-z]?',
            r'show\s+(?:the\s+)?marks?\s+(?:sheet\s+)?(?:for\s+|of\s+)?class\s+\d+\s*[a-z]?',
            r'go\s+to\s+(?:the\s+)?marks?\s+(?:sheet\s+)?(?:for\s+|of\s+)?class\s+\d+\s*[a-z]?',
            r'display\s+(?:the\s+)?marks?\s+(?:sheet\s+)?(?:for\s+|of\s+)?class\s+\d+\s*[a-z]?',
            # Ordinal: "open 1st A marks" or "open 2nd B marks sheet"
            r'open\s+(?:the\s+)?(\d+)(?:st|nd|rd|th)\s*([a-z])?\s+marks?',
            # Short: "open class 1A marks" or "open 1A marks"
            r'open\s+(?:class\s+)?(\d+)\s*([a-z])\s+marks?',
            # With section keyword: "open marks class 1 section A"
            r'open\s+(?:the\s+)?marks?\s+(?:for\s+)?class\s+(\d+)\s+section\s+([a-z])',
            # Go to patterns: "go to class 1A marks" or "go to 1A marksheet"
            r'go\s+to\s+(?:class\s+)?(\d+)\s*([a-z])\s+marks?',
            r'go\s+to\s+(\d+)(?:st|nd|rd|th)\s*([a-z])?\s+marks?',
            # SHORT FORMS: "open 2nd c" or "open 2c" (no "marks" keyword needed)
            # These are used when already on marks list page
            r'^open\s+(\d+)(?:st|nd|rd|th)\s+([a-z])[\s\.,;!?]*$',  # "open 2nd c"
            r'^open\s+(?:class\s+)?(\d+)\s*([a-z])[\s\.,;!?]*$',  # "open 2c" or "open class 2c"
            r'^go\s+to\s+(\d+)(?:st|nd|rd|th)\s+([a-z])[\s\.,;!?]*$',  # "go to 2nd c"
            r'^go\s+to\s+(?:class\s+)?(\d+)\s*([a-z])[\s\.,;!?]*$',  # "go to 2c" or "go to class 2c"
            # With "section" keyword and ordinal: "open class 3rd section B", "open 3rd section b"
            r'open\s+(?:class\s+)?\d+(?:st|nd|rd|th)\s+section\s+[a-z]',
            r'go\s+to\s+(?:class\s+)?\d+(?:st|nd|rd|th)\s+section\s+[a-z]',
            r'show\s+(?:class\s+)?\d+(?:st|nd|rd|th)\s+section\s+[a-z]',
            # With "section" keyword and number: "open class 3 section B"
            r'open\s+(?:class\s+)?\d+\s+section\s+[a-z]',
            r'go\s+to\s+(?:class\s+)?\d+\s+section\s+[a-z]',
            # SUPER SHORT: "marks 1a" or "1a marks" or just "1a"
            r'^marks?\s+(\d+)\s*([a-z])[\s\.,;!?]*$',  # "marks 1a"
            r'^(\d+)\s*([a-z])\s+marks?[\s\.,;!?]*$',  # "1a marks"
            r'^(\d+)\s*([a-z])[\s\.,;!?]*$',  # just "1a" or "2b"
            # SPELLED ORDINALS with section: "open first B" or "open second A"
            r'^open\s+(?:class\s+)?(first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth)\s+([a-z])[\s\.,;!?]*$',
            r'^go\s+to\s+(?:class\s+)?(first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth)\s+([a-z])[\s\.,;!?]*$',
            # WITH EXAM TYPE: "open first B final term" or "open 1B midterm" or "open class 2A unit test"
            r'open\s+(?:class\s+)?(first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth|\d+)\s*([a-z])\s+(?:mid\s*term|midterm|final(?:\s+term)?|unit\s*test|unittest)',
            r'open\s+(?:class\s+)?(\d+)(?:st|nd|rd|th)\s*([a-z])\s+(?:mid\s*term|midterm|final(?:\s+term)?|unit\s*test|unittest)',
            # Go to with exam type
            r'go\s+to\s+(?:class\s+)?(first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth|\d+)\s*([a-z])\s+(?:mid\s*term|midterm|final(?:\s+term)?|unit\s*test|unittest)',
            # Flexible for noise: just ordinal + section + exam (no "open" prefix)
            r'^(first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth)\s+([a-z])\s+(?:mid\s*term|midterm|final(?:\s+term)?|unit\s*test|unittest)[\s\.,;!?]*$',
            r'^(\d+)\s*([a-z])\s+(?:mid\s*term|midterm|final(?:\s+term)?|unit\s*test|unittest)[\s\.,;!?]*$',
        ],
        'OPEN_ATTENDANCE_SHEET': [
            # Standard: "open attendance for class 1A" or "open attendance for class 1 A"
            r'open\s+(?:the\s+)?attendance\s+(?:sheet\s+)?(?:for\s+|of\s+)?class\s+\d+\s*[a-z]?',
            r'show\s+(?:the\s+)?attendance\s+(?:sheet\s+)?(?:for\s+|of\s+)?class\s+\d+\s*[a-z]?',
            r'go\s+to\s+(?:the\s+)?attendance\s+(?:sheet\s+)?(?:for\s+|of\s+)?class\s+\d+\s*[a-z]?',
            r'display\s+(?:the\s+)?attendance\s+(?:sheet\s+)?(?:for\s+|of\s+)?class\s+\d+\s*[a-z]?',
            # Ordinal: "open 1st A attendance" or "open 2nd B attendance sheet"
            r'open\s+(?:the\s+)?(\d+)(?:st|nd|rd|th)\s*([a-z])?\s+attendance',
            # Short: "open class 1A attendance" or "open 1A attendance"
            r'open\s+(?:class\s+)?(\d+)\s*([a-z])\s+attendance',
            # With section keyword: "open attendance class 1 section A"
            r'open\s+(?:the\s+)?attendance\s+(?:for\s+)?class\s+(\d+)\s+section\s+([a-z])',
            # Go to patterns: "go to class 1A attendance" or "go to 1A attendance"
            r'go\s+to\s+(?:class\s+)?(\d+)\s*([a-z])\s+attendance',
            r'go\s+to\s+(\d+)(?:st|nd|rd|th)\s*([a-z])?\s+attendance',
            # With "section" keyword: "open class 3rd section B attendance"
            r'open\s+(?:class\s+)?\d+(?:st|nd|rd|th)\s+section\s+[a-z]\s+attendance',
            r'go\s+to\s+(?:class\s+)?\d+(?:st|nd|rd|th)\s+section\s+[a-z]\s+attendance',
            r'open\s+(?:class\s+)?\d+\s+section\s+[a-z]\s+attendance',
            # SUPER SHORT: "attendance 1a" or "1a attendance"
            r'^attendance\s+(\d+)\s*([a-z])[\s\.,;!?]*$',  # "attendance 1a"
            r'^(\d+)\s*([a-z])\s+attendance[\s\.,;!?]*$',  # "1a attendance"
        ],
        # General navigation (after attendance marking)
        'NAVIGATE_MARKS': [
            r'^open\s+marks?[\s\.,;!?]*$',
            r'^show\s+marks?[\s\.,;!?]*$',
            r'^open\s+(?:the\s+)?marks?\s*(?:page|list|sheet)?[\s\.,;!?]*$',
            r'^show\s+(?:the\s+)?marks?\s*(?:page|list|sheet)?[\s\.,;!?]*$',
            r'^go\s+to\s+(?:the\s+)?marks?\s*(?:page|list|sheet)?[\s\.,;!?]*$',
            # Single word: just "marks" or "marksheet"
            r'^marks?[\s\.,;!?]*$',
            r'^marksheet[\s\.,;!?]*$',
            r'^go\s+to\s+(?:the\s+)?marksheet[\s\.,;!?]*$',
            r'navigate\s+to\s+(?:the\s+)?marks?',
            # Marksheet as single word (no space)
            r'^go\s+to\s+marksheet$',
            r'^open\s+marksheet$',
            r'go\s+to\s+marksheet',
            r'open\s+marksheet',
            r'go\s+to\s+marks\s*sheet',
        ],
        'NAVIGATE_ATTENDANCE': [
            r'^open\s+attendance[\s\.,;!?]*$',
            r'^show\s+attendance[\s\.,;!?]*$',
            r'^open\s+(?:the\s+)?attendance\s*(?:page|list|sheet)?[\s\.,;!?]*$',
            r'^show\s+(?:the\s+)?attendance\s*(?:page|list|sheet)?[\s\.,;!?]*$',
            r'^go\s+to\s+(?:the\s+)?attendance\s*(?:page|list|sheet)?[\s\.,;!?]*$',
            r'navigate\s+to\s+(?:the\s+)?attendance',
            # Simple patterns without anchors
            r'go\s+to\s+attendance$',
            r'open\s+attendance\s+sheet$',
            # Single word: just "attendance"
            r'^attendance[\s\.,;!?]*$',
        ],
        # Dashboard navigation
        'NAVIGATE_DASHBOARD': [
            r'^go\s+to\s+(?:the\s+)?dashboard[\s\.,;!?]*$',
            r'^open\s+(?:the\s+)?dashboard[\s\.,;!?]*$',
            r'^show\s+(?:the\s+)?dashboard[\s\.,;!?]*$',
            r'go\s+to\s+dashboard',
            r'open\s+dashboard',
            r'navigate\s+to\s+(?:the\s+)?dashboard',
            r'^dashboard[\s\.,;!?]*$',
            r'^go\s+(?:to\s+)?home[\s\.,;!?]*$',
            r'^go\s+back[\s\.,;!?]*$',
            r'^home[\s\.,;!?]*$',
        ],
        # Navigate to specific report tabs (MUST be before general NAVIGATE_REPORTS)
        'NAVIGATE_CLASS_REPORT': [
            r'open\s+(?:the\s+)?class\s+reports?',
            r'show\s+(?:the\s+)?class\s+reports?',
            r'go\s+to\s+(?:the\s+)?class\s+reports?',
            r'view\s+(?:the\s+)?class\s+reports?',
            r'class\s+reports?\s+(?:tab|page|section)',
            r'^class\s+reports?[\s\.,;!?]*$',
            # Super short: just "class report"
            r'^class\s+report[\s\.,;!?]*$',
            # Shortcuts: "classes", "all classes"
            r'^classes[\s\.,;!?]*$',
            r'^all\s+classes[\s\.,;!?]*$',
            r'^class\s+stats?[\s\.,;!?]*$',
            r'^class\s+summary[\s\.,;!?]*$',
        ],
        'NAVIGATE_STUDENT_REPORT': [
            r'open\s+(?:the\s+)?student\s+reports?',
            r'show\s+(?:the\s+)?student\s+reports?',
            r'go\s+to\s+(?:the\s+)?student\s+reports?',
            r'view\s+(?:the\s+)?student\s+reports?',
            r'student\s+reports?\s+(?:tab|page|section)',
            r'^student\s+reports?[\s\.,;!?]*$',
            # Super short: just "student report"
            r'^student\s+report[\s\.,;!?]*$',
            # Shortcuts: "students", "all students"
            r'^students[\s\.,;!?]*$',
            r'^all\s+students[\s\.,;!?]*$',
            r'^student\s+stats?[\s\.,;!?]*$',
            r'^student\s+summary[\s\.,;!?]*$',
        ],
        'NAVIGATE_ATTENDANCE_REPORT': [
            r'open\s+(?:the\s+)?attendance\s+reports?',
            r'show\s+(?:the\s+)?attendance\s+reports?',
            r'go\s+to\s+(?:the\s+)?attendance\s+reports?',
            r'view\s+(?:the\s+)?attendance\s+reports?',
            r'attendance\s+reports?\s+(?:tab|page|section)',
            r'attendance\s+(?:tab|analytics)',
            r'^attendance\s+report[\s\.,;!?]*$',
            # Super short variations
            r'^attendance\s+stats?[\s\.,;!?]*$',
            r'^attendance\s+summary[\s\.,;!?]*$',
        ],
        # Navigate to Reports & Analytics (general - overview tab)
        'NAVIGATE_REPORTS': [
            r'^open\s+(?:the\s+)?reports?[\s\.,;!?]*$',
            r'^show\s+(?:the\s+)?reports?[\s\.,;!?]*$',
            r'^go\s+to\s+(?:the\s+)?reports?[\s\.,;!?]*$',
            r'^open\s+(?:the\s+)?analytics[\s\.,;!?]*$',
            r'^show\s+(?:the\s+)?analytics[\s\.,;!?]*$',
            r'^go\s+to\s+(?:the\s+)?analytics[\s\.,;!?]*$',
            r'navigate\s+to\s+(?:the\s+)?reports?',
            r'open\s+reports?\s+(?:and\s+)?analytics',
            r'show\s+reports?\s+(?:and\s+)?analytics',
            r'^reports?[\s\.,;!?]*$',
            r'^analytics[\s\.,;!?]*$',
            r'view\s+(?:the\s+)?reports?',
            r'view\s+(?:the\s+)?analytics',
            # Flexible patterns for speech recognition errors
            r'\breport\b.*\banalytics?\b',  # "report" followed eventually by "analytics"
            r'\banalytics?\b.*\breport\b',  # "analytics" followed by "report"
            r'\breports?\s+(?:page|section|tab)',  # "reports page/section"
            r'\banalytics?\s+(?:page|section|tab)',  # "analytics page/section"
            # Shortcuts: "overview", "stats", "summary"
            r'^overview[\s\.,;!?]*$',
            r'^stats[\s\.,;!?]*$',
            r'^statistics[\s\.,;!?]*$',
            r'^summary[\s\.,;!?]*$',
            r'^show\s+overview[\s\.,;!?]*$',
            r'^show\s+stats[\s\.,;!?]*$',
        ],
        # ============================================================
        # FEE MANAGEMENT INTENTS (for ACCOUNTANT role)
        # ============================================================
        # Fee collection (MUST be before OPEN_FEE_PAGE)
        'COLLECT_FEE': [
            r'collect\s+(?:fee|fees|payment)',
            r'collect\s+\d+\s+(?:from|for)',
            r'collect\s+(?:rupees?\s+)?\d+',
            r'fee\s+collect(?:ion)?\s+(?:from|for)',
            r'take\s+(?:fee|fees|payment)\s+(?:from|for|of)',
            r'receive\s+(?:fee|fees|payment)',
            r'accept\s+(?:fee|fees|payment)',
            # Amount patterns: "collect 5000 from roll 12 class 6A cash"
            r'collect\s+(?:rupees?\s+)?\d+\s+(?:from|for)\s+(?:roll|student|rule)',
            # Amount-first: "5000 from roll 12", "rupees 5000 from student 12"
            r'(?:rupees?\s+)?\d+\s+(?:from|for)\s+(?:roll|student|rule)\s+\d+',
            # Collect from student: "collect from roll 12", "collect fee for student 5"
            r'collect\s+(?:fee\s+)?(?:from|for)\s+(?:roll|student|rule)\s+\d+',
            # Payment method + amount: "collect 5000 cash", "5000 in cash"
            r'collect\s+(?:rupees?\s+)?\d+\s+(?:in\s+)?(?:cash|cheque|online|upi|card)',
            # Polite/contextual: "I want to collect", "let me collect", "please collect"
            r'(?:i\s+)?(?:want\s+to|need\s+to|would\s+like\s+to)\s+collect\s+(?:fee|fees|payment|\d+)',
            r'(?:let\s+me|please)\s+collect\s+(?:fee|fees|payment|\d+)',
            # Hindi patterns
            r'fees?\s+(?:le\s+lo|lelo|lo)',
            r'paisa\s+(?:le\s+lo|lelo|lo)',
            r'(?:roll|student)\s+\d+\s+(?:ka|ke|ki)\s+(?:fee|fees|paisa)\s+(?:lo|lelo|le\s+lo)',
            r'(?:rupees?\s+)?\d+\s+(?:roll|student)\s+\d+\s+(?:se|ka)\s+(?:lo|lelo)',
            r'(?:jaama|jama)\s+(?:karo|kar\s+do|kar)',
            r'paisa\s+(?:nikalo|nikaal)',
            r'fee\s+(?:bharo|jama\s+karo|le\s+lo)',
            # Student name-based: "collect fee from Rahul", "take fee from Amit", "collect fee 5000 from Rahul"
            r'collect\s+(?:fee|fees|payment)\s+(?:(?:rupees?\s+)?\d+\s+)?(?:from|for|of)\s+[a-z]+',
            r'take\s+(?:fee|fees|payment)\s+(?:(?:rupees?\s+)?\d+\s+)?(?:from|for|of)\s+[a-z]+',
            # Fee type: "collect tuition fee", "transport fee collection", "bus fee lo"
            r'collect\s+(?:tuition|transport|bus|hostel|exam|admission|lab|library|annual)\s+(?:fee|fees)',
            r'(?:tuition|transport|bus|hostel|exam|admission|lab|library|annual)\s+(?:fee|fees)\s+(?:collect|lo|lelo|le\s+lo|bharo)',
            # Natural conversation: "fee payment", "process payment"
            r'(?:fee|fees)\s+payment\s+(?:for|from|of)',
            r'(?:process|make|do|enter|record)\s+(?:a\s+)?(?:fee\s+)?payment',
            r'(?:student|roll|rule)\s+\d+\s+(?:came\s+to\s+)?pay',
            r'(?:student|roll|rule)\s+\d+\s+(?:wants?\s+to|has\s+come\s+to)\s+pay',
            # Amount with class+roll: "5000 from class 5 roll 12", "collect 3000 class 6A roll 5"
            r'(?:collect\s+)?(?:rupees?\s+)?\d+\s+(?:from\s+)?class\s+\d+\s*[a-z]?\s+(?:roll|student)\s+\d+',
            # Partial/half payment: "collect half fee", "partial fee payment"
            r'collect\s+(?:half|partial|remaining|pending)\s+(?:fee|fees|payment|amount)',
            r'(?:half|partial|remaining|pending)\s+(?:fee|fees|payment|amount)\s+(?:collect|lo|lelo)',
            # Pay/paid triggers: "roll 5 wants to pay", "student paying fees"
            r'(?:roll|student|rule)\s+\d+\s+(?:is\s+)?(?:paying|pay)',
            r'(?:pay|paying)\s+(?:fee|fees)\s+(?:for\s+)?(?:roll|student|rule)\s+\d+',
            # Hindi extended: "fee dena hai", "fee lena hai", "bharwa do"
            r'fee\s+(?:dena|lena)\s+(?:hai|hain)',
            r'fee\s+de\s+(?:do|\d+)',  # "fee de do" (do→2 after normalization)
            r'fee\s+(?:bharwa|jama\s+karwa)\s+(?:do|\d+)',
            r'(?:roll|student)\s+\d+\s+(?:ka|ke|ki)\s+(?:fee|fees|paisa)\s+(?:bharo|jama\s+karo)',
            r'(?:roll|student)\s+\d+\s+(?:se|ka)\s+(?:paisa|fee|fees)\s+(?:le\s+lo|lelo|lo|collect)',
            # Amount with payment method variants: "5000 by UPI", "3000 through cash"
            r'(?:rupees?\s+)?\d+\s+(?:by|through|via|in)\s+(?:cash|cheque|online|upi|card|neft)',
            # Deposit/submit fee
            r'(?:deposit|submit)\s+(?:fee|fees|payment)',
            r'(?:fee|fees)\s+(?:deposit|submission)',
            # Implicit collection: amount + roll/student + class (no "collect" verb)
            r'(?:rupees?\s+)?\d{3,}\s+(?:roll|student|rule)\s+(?:number\s+)?\d+\s+class',
            r'(?:rupees?\s+)?\d{3,}\s+(?:from\s+)?(?:roll|student|rule)\s+(?:number\s+)?\d+',
        ],
        # Open fee page for specific class
        'OPEN_FEE_PAGE': [
            r'open\s+(?:the\s+)?(?:fee|fees)\s+(?:for\s+|of\s+)?class\s+\d+\s*[a-z]?',
            r'show\s+(?:the\s+)?(?:fee|fees)\s+(?:for\s+|of\s+)?class\s+\d+\s*[a-z]?',
            r'go\s+to\s+(?:the\s+)?(?:fee|fees)\s+(?:for\s+|of\s+)?class\s+\d+\s*[a-z]?',
            r'open\s+(?:class\s+)?(\d+)\s*([a-z])\s+(?:fee|fees)',
            r'(?:fee|fees)\s+(?:page|list|status)\s+(?:for\s+)?class\s+\d+',
            r'^open\s+(?:fee|fees)[\s\.,;!?]*$',
            r'^show\s+(?:fee|fees)[\s\.,;!?]*$',
            r'^go\s+to\s+(?:fee|fees)[\s\.,;!?]*$',
            r'^(?:fee|fees)[\s\.,;!?]*$',
            r'^(?:fee|fees)\s+(?:page|list|management|tab|section)[\s\.,;!?]*$',
            # Fee collection navigation (not actual collection — no amount/student)
            r'(?:open|show|go\s+to|view|see)\s+(?:the\s+)?(?:fee\s+)?collections?[\s\.,;!?]*$',
            r'(?:open|show|go\s+to|view|see)\s+(?:the\s+)?fee\s+collect(?:ion|ions)[\s\.,;!?]*$',
            r'(?:to\s+)?see\s+(?:the\s+)?(?:fee\s+)?collections?[\s\.,;!?]*$',
            r'^(?:fee\s+)?collections?[\s\.,;!?]*$',
            r'^(?:fee\s+)?collection\s+(?:page|list|tab)[\s\.,;!?]*$',
            r'(?:open|show|go\s+to|view)\s+(?:the\s+)?fee\s+(?:payment|payments?)[\s\.,;!?]*$',
            # Polite forms: "please open fees", "take me to fees"
            # MUST NOT match fee+report/analytics — use negative lookahead
            r'(?:please\s+)?(?:can\s+you\s+)?(?:open|show)\s+(?:the\s+)?(?:fee|fees)(?!\s+(?:report|analytics|analysis|summary|statistics|stats|breakdown|dashboard|trend))[\s\.,;!?]*$',
            r'(?:take|bring)\s+(?:me\s+)?(?:to\s+)?(?:the\s+)?(?:fee|fees)[\s\.,;!?]*$',
            r'display\s+(?:the\s+)?(?:fee|fees)[\s\.,;!?]*$',
            # Class+section: "4A fees", "5B fee", "go to 5A"
            r'^\d+\s*[a-z]\s+(?:fee|fees)[\s\.,;!?]*$',
            r'(?:open|go\s+to|show|view)\s+(?:the\s+)?\d+\s*[a-z]\s+(?:fee|fees)',
            r'(?:fee|fees)\s+(?:for\s+|of\s+)?\d+\s*[a-z]',
            # Class with section keyword: "class 4 section A"
            r'(?:open|go\s+to|show)\s+(?:the\s+)?class\s+\d+\s+section\s+[a-z]',
            # Class-specific navigation (accountant context: "open 4th", "class 4th", "open class 4")
            r'(?:open|go\s+to|view|show)\s+(?:the\s+)?(?:class\s+)?\d+(?:st|nd|rd|th)[\s\.,;!?]*$',
            r'(?:open|go\s+to|view|show)\s+(?:the\s+)?class\s+\d+[\s\.,;!?]*$',
            r'^class\s+\d+(?:st|nd|rd|th)?[\s\.,;!?]*$',
            r'^\d+(?:st|nd|rd|th)\s+(?:class)?[\s\.,;!?]*$',
            r'(?:open|go\s+to|view|show)\s+(?:the\s+)?\d+(?:st|nd|rd|th)\s+class[\s\.,;!?]*$',
            # Class with section after ordinal: "open 4th A", "go to 5th B"
            r'(?:open|go\s+to|view|show)\s+(?:the\s+)?(?:class\s+)?\d+(?:st|nd|rd|th)\s+[a-z][\s\.,;!?]*$',
            r'(?:open|go\s+to|view|show)\s+(?:the\s+)?class\s+\d+\s+[a-z][\s\.,;!?]*$',
            # Hindi: "fee kholo", "fees dikhao" (but NOT "baki fees dikhao" — that's defaulters)
            r'(?<!baki\s)(?<!baaki\s)(?:fee|fees)\s+(?:kholo|dikhao|dikha\s+do|batao)',
            r'(?:fee|fees)\s+(?:ka|ki)\s+(?:page|list)',
        ],
        # Show defaulters
        'SHOW_DEFAULTERS': [
            r'show\s+(?:the\s+)?defaulters?',
            r'(?:list|display|view|check)\s+(?:the\s+)?defaulters?',
            r'(?:who|which)\s+(?:students?\s+)?(?:has|have)(?:n\'?t)?\s+(?:not\s+)?paid',
            r'defaulters?\s+(?:list|for|in|of)\s+class',
            r'unpaid\s+(?:fee|fees|students?)',
            r'pending\s+(?:fee|fees|dues?)\s+(?:list|students?)',
            r'^defaulters?[\s\.,;!?]*$',
            r'show\s+defaulters?\s+(?:for\s+|of\s+|in\s+)?class\s+\d+',
            r'(?:fee|fees)\s+defaulters?',
            # Class-specific: "defaulters in class 4", "class 5 defaulters"
            r'(?:defaulters?|unpaid|pending)\s+(?:in|of|for|from)\s+(?:class\s+)?\d+(?:\s*[a-z])?',
            r'(?:class\s+)?\d+(?:\s*[a-z])?\s+(?:ke?\s+)?defaulters?',
            # Who owes: "who owes fees", "who hasn't given fees"
            r'(?:who|which)\s+(?:all\s+)?(?:students?\s+)?(?:owes?|owe)\s+(?:us\s+)?(?:fee|fees|money)',
            r'(?:who|which)\s+(?:all\s+)?(?:students?\s+)?(?:has|have)(?:n\'?t)?\s+(?:given|submitted)\s+(?:fee|fees)',
            # Outstanding/arrears
            r'(?:show|display|list|check)\s+(?:the\s+)?(?:outstanding|arrears|overdue)',
            r'(?:outstanding|overdue|remaining|pending)\s+(?:dues?|fees?|amount)',
            r'(?:non[\s-]?payers?|non[\s-]?paying)(?:\s+(?:students?|list))?',
            # Hindi patterns
            r'(?:baaki|baki)\s+(?:fees?|paisa|wale|students?|list)',
            r'(?:fees?|paisa)\s+(?:de\s+)?(?:nahi|na)\s+(?:diye|diya|dene)',
            r'(?:fees?|paisa)\s+nahi\s+(?:bhara|bharaa|paid|diya)',
            r'(?:baki|baaki)\s+(?:waale|wale|log)',
            # "baki fees dikhao" — must match SHOW_DEFAULTERS not OPEN_FEE_PAGE
            r'(?:baki|baaki)\s+(?:fees?|paisa)\s+(?:dikhao|dikha\s+do|batao|bata)',
            r'(?:baki|baaki)\s+(?:fees?|paisa)\s+(?:kaun|kiska|kiski|kiske)',
        ],
        # Today's collection
        'TODAY_COLLECTION': [
            r'today\'?s?\s+collection',
            r'today\'?s?\s+(?:fee\s+)?collection',
            r'(?:show|display|view|get|check|tell)\s+(?:me\s+)?today\'?s?\s+collection',
            r'how\s+much\s+(?:collected|received|collection)\s+today',
            r'total\s+collection\s+today',
            r'collection\s+(?:for\s+)?today',
            r'^today\'?s?\s+(?:total|summary|report)[\s\.,;!?]*$',
            # What's the collection: "what's the collection today", "what is today's total"
            r'(?:what\'?s?|what\s+is)\s+(?:the\s+)?(?:total\s+)?collection\s+(?:for\s+)?today',
            r'(?:what\'?s?|what\s+is)\s+today\'?s?\s+(?:total|collection|amount)',
            r'(?:tell|show|check)\s+(?:me\s+)?(?:the\s+)?(?:total\s+)?(?:collection|amount)\s+(?:for\s+)?today',
            # So far / till now (implies "today")
            r'(?:total\s+)?collection\s+(?:so\s+far|till\s+now|until\s+now)',
            r'^collection\s+(?:so\s+far|till\s+now)[\s\.,;!?]*$',
            r'(?:total|how\s+much)\s+(?:so\s+far|till\s+now)\s+today',
            # Hindi patterns
            r'(?:aaj|aaj\s+ka|aaj\s+ki)\s+(?:collection|total|paisa|fees?)',
            r'(?:kitna|kitni)\s+(?:collection|fees?|paisa)\s+(?:aaj|today)',
            r'(?:aaj|today)\s+(?:kitna|kitni|total)\s+(?:hua|huaa|ho\s+gaya)',
            r'(?:aaj|today)\s+(?:ka|ki)\s+(?:total|collection|paisa|fees?)',
            r'(?:aaj|today)\s+(?:collection|paisa)\s+(?:kitna|kya|batao|bata|dikhao)',
        ],
        # Navigate to fee reports
        'NAVIGATE_FEE_REPORTS': [
            r'(?:open|show|go\s+to|view)\s+(?:the\s+)?fee\s+reports?',
            r'(?:open|show|go\s+to|view)\s+(?:the\s+)?(?:fee|fees)\s+(?:analytics|analysis|summary|dashboard|statistics|stats)',
            r'^fee\s+reports?[\s\.,;!?]*$',
            r'(?:fee|fees)\s+(?:report|analytics|analysis|summary|statistics|stats|dashboard)',
            r'(?:open|show)\s+(?:the\s+)?collection\s+reports?',
            r'monthly\s+(?:fee\s+)?(?:collection|report|trend)',
            r'class[\s-]?wise\s+(?:fee\s+)?(?:collection|report)',
            # More report types
            r'(?:open|show|view)\s+(?:the\s+)?(?:fee|collection)\s+(?:breakdown|distribution|trend)',
            r'(?:weekly|monthly|yearly)\s+(?:fee\s+|collection\s+)?(?:report|trend|summary)',
            r'(?:student|section)[\s-]?wise\s+(?:fee\s+)?(?:collection|report)',
            r'(?:collection|payment)\s+(?:summary|overview|analysis|report)',
            # Shorthand
            r'^(?:fee\s+)?(?:analytics?|analysis|statistics|stats)[\s\.,;!?]*$',
            # Hindi patterns
            r'(?:fee|fees|collection|paisa)\s+(?:ki|ka)\s+(?:report|details?|summary)',
            r'(?:report|analytics)\s+(?:dikhao|dikha\s+do|batao)',
        ],
        # Select exam type for marks (MUST be before DOWNLOAD_PROGRESS_REPORT)
        'SELECT_EXAM_TYPE': [
            # Midterm patterns (handles noise/mishearings normalized to "midterm")
            r'(?:open|show|go\s+to|select)\s+(?:the\s+)?(?:first\s+)?mid\s*term',
            r'(?:open|show|go\s+to|select)\s+(?:the\s+)?midterm(?:\s+exam)?',
            r'(?:open|show|go\s+to|select)\s+(?:the\s+)?mid\s+term\s+exam',
            r'^mid\s*term(?:\s+exam)?[\s\.,;!?]*$',
            r'^midterm(?:\s+exam)?[\s\.,;!?]*$',
            r'^first\s+mid\s*term[\s\.,;!?]*$',
            # Final exam patterns
            r'(?:open|show|go\s+to|select)\s+(?:the\s+)?final(?:\s+term)?(?:\s+exam)?',
            r'(?:open|show|go\s+to|select)\s+(?:the\s+)?finals?',
            r'^final(?:\s+term)?(?:\s+exam)?[\s\.,;!?]*$',
            r'^finals?[\s\.,;!?]*$',
            # Unit test patterns (handles normalized "unittest" without space)
            r'(?:open|show|go\s+to|select)\s+(?:the\s+)?unit\s*test',
            r'(?:open|show|go\s+to|select)\s+(?:the\s+)?unittest',
            r'^unit\s*test[\s\.,;!?]*$',
            r'^unittest[\s\.,;!?]*$',
            # Generic exam selection with type
            r'(?:open|show|select)\s+(?:the\s+)?(?:marks?\s+(?:for|of)\s+)?(?:mid\s*term|midterm|final|unit\s*test|unittest)',
        ],
        # Download progress report
        'DOWNLOAD_PROGRESS_REPORT': [
            r'download\s+(?:the\s+)?(?:progress\s+)?report',
            r'download\s+(?:the\s+)?report\s+(?:card|sheet)',
            r'generate\s+(?:the\s+)?(?:progress\s+)?report',
            r'export\s+(?:the\s+)?(?:progress\s+)?report',
            r'get\s+(?:the\s+)?(?:progress\s+)?report',
            r'print\s+(?:the\s+)?(?:progress\s+)?report',
            r'(?:progress\s+)?report\s+(?:for\s+)?(?:student|roll)',
            r'student\s+report\s+(?:card|sheet)',
        ],
        # Fee details for a student (MUST be before VIEW_STUDENT)
        'SHOW_FEE_DETAILS': [
            r'(?:show|view|get|check|display|generate)\s+(?:the\s+)?(?:fee|fees)\s+(?:details?|info|status|summary|receipts?)\s+(?:of|for)\s+(?:student|roll|rule)',
            r'(?:show|view|get|check|display|generate)\s+(?:the\s+)?(?:fee|fees)\s+(?:of|for)\s+(?:student|roll|rule)',
            r'(?:fee|fees)\s+(?:details?|info|status|summary|receipts?)\s+(?:of|for)\s+(?:student|roll|rule)',
            r'(?:fee|fees)\s+(?:details?|info|status|receipts?)\s+(?:of|for)\s+(?:roll|student|rule)\s+(?:number\s+)?\d+',
            # "generate fee receipt of student 2", "fee receipt student 5"
            r'(?:generate|show|get|print)\s+(?:the\s+)?(?:fee\s+)?receipts?\s+(?:of|for)\s+(?:student|roll|rule)',
            r'(?:fee\s+)?receipts?\s+(?:of|for)\s+(?:student|roll|rule)\s+(?:number\s+)?\d+',
            r'(?:student|roll|rule)\s+(?:number\s+)?\d+\s+(?:ka|ke|ki)\s+(?:fee|fees)\s+(?:details?|status|info)',
            r'(?:how\s+much|kitna|kitni)\s+(?:fee|fees|dues?|pending|baki)\s+(?:for|of)\s+(?:student|roll|rule)',
            r'(?:student|roll|rule)\s+(?:number\s+)?\d+\s+(?:fee|fees)\s+(?:details?|status|info|pending|dues?)',
            r'(?:check|show)\s+(?:fee|fees)\s+(?:for\s+)?(?:student|roll|rule)\s+(?:number\s+)?\d+',
            # Hindi: "roll 5 ki fee batao", "student 2 ka fee status"
            r'(?:student|roll|rule)\s+(?:number\s+)?\d+\s+(?:ka|ke|ki)\s+(?:fee|fees|paisa)',
            r'(?:fee|fees|paisa)\s+(?:batao|dikhao|bata)\s+(?:student|roll|rule)\s+(?:number\s+)?\d+',
            # Without of/for: "fee details student 3", "fee status roll 5"
            r'(?:fee|fees)\s+(?:details?|info|status|summary)\s+(?:student|roll|rule)\s+(?:number\s+)?\d+',
            r'(?:fee|fees)\s+(?:details?|info|status)\s+(?:student|roll|rule)',
            # "how much pending for roll 5", "kitna baki hai roll 3", "kitna fee pending hai student 3"
            r'(?:how\s+much|kitna|kitni)\s+(?:(?:fee|fees|dues?|pending|baki|hai)\s+){1,3}(?:student|roll|rule)',
            # Whisper mishearing: "show fee details are student" (are → of)
            r'(?:show|view|get|check)\s+(?:the\s+)?(?:fee|fees)\s+(?:details?|info|status)\s+(?:are|off)\s+(?:student|roll|rule)',
            # Very short: just "fee details" with context providing class/student
            r'^(?:fee|fees)\s+(?:details?|info|status)\s+(?:of|for|are)?\s*(?:student|roll|rule)\s+(?:number\s+)?\d+[\s\.,;!?]*$',
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

    # ============================================================
    # EDGE CASE HANDLING: Section 1 - Homophones & Similar Sounds
    # ============================================================
    HOMOPHONES = {
        # Number homophones (context-sensitive - handled separately)
        'won': '1', 'wan': '1',
        'too': '2', 'tu': '2',
        'tree': '3',  # Accent variation
        # NOTE: 'free' removed — context-sensitive (could be "fee" or "3"); handled in normalize_stt_text
        'fore': '4', 'foor': '4',
        'hive': '5',  # Mishearing
        'sex': '6', 'sax': '6',  # Mishearing
        'ate': '8', 'eat': '8', 'ait': '8',
        'nein': '9', 'nine': '9',

        # Common word mishearings
        'rule': 'roll', 'role': 'roll', 'rool': 'roll', 'rol': 'roll',
        'max': 'marks', 'marx': 'marks', 'mux': 'marks',
        'stew dent': 'student', 'stew dint': 'student',
    }

    # ============================================================
    # EDGE CASE HANDLING: Section 2 - Subject Name Mishearings
    # ============================================================
    SUBJECT_MISHEARINGS = {
        # Mathematics variations (Indian accent tends to soften 'th')
        'mass': 'maths', 'match': 'maths', 'moths': 'maths', 'mats': 'maths',
        'mouth': 'maths', 'math': 'maths', 'meth': 'maths', 'mess': 'maths',
        'mathematics': 'maths', 'mathematic': 'maths', 'mats': 'maths',
        'madds': 'maths', 'mads': 'maths', 'matts': 'maths', 'max': 'maths',
        'meth emetics': 'maths', 'methematics': 'maths',

        # Hindi variations (common STT confusions)
        'indy': 'hindi', 'indie': 'hindi', 'hind': 'hindi', 'hendy': 'hindi',
        'hindy': 'hindi', 'indi': 'hindi', 'hindu': 'hindi', 'handy': 'hindi',
        'hundi': 'hindi', 'hendy': 'hindi', 'hindy': 'hindi',

        # English variations (Indian pronunciation)
        'in glitch': 'english', 'ang lish': 'english', 'enlist': 'english',
        'inglish': 'english', 'englis': 'english', 'anglish': 'english',
        'english language': 'english', 'eng': 'english', 'inglis': 'english',

        # Science variations
        'signs': 'science', 'silence': 'science', 'sigh ants': 'science',
        'sience': 'science', 'scince': 'science', 'sins': 'science',
        'sciens': 'science', 'signes': 'science', 'sines': 'science',
        'since': 'science', 'sens': 'science', 'sains': 'science',
        'sence': 'science', 'scence': 'science', 'sinse': 'science', 'sin': 'science',

        # Social Studies variations
        'so shall': 'social', 'so shell': 'social', 'soshul': 'social',
        'social studied': 'social studies', 'so shall studies': 'social studies',
        'social study': 'social studies', 'sst': 'social studies',
        'ss': 'social studies', 'social science': 'social studies',

        # Computer variations
        'compote': 'computer', 'come pewter': 'computer', 'komputer': 'computer',
        'computer science': 'computer', 'comp': 'computer', 'cs': 'computer',
    }

    # ============================================================
    # EDGE CASE: Ordinal Number Mishearings (for noisy environments)
    # ============================================================
    ORDINAL_MISHEARINGS = {
        # First variations
        'fast': 'first', 'fist': 'first', 'feast': 'first', 'forced': 'first',
        'furst': 'first', 'farst': 'first', 'firs': 'first', 'furst': 'first',
        '1st': 'first', 'frist': 'first', 'forst': 'first',
        # Second variations
        'seconds': 'second', 'sekund': 'second', 'sekond': 'second',
        'secund': 'second', 'sacond': 'second', '2nd': 'second', 'secnd': 'second',
        # Third variations
        'thrid': 'third', 'tird': 'third', '3rd': 'third', 'thurd': 'third',
        'therd': 'third', 'tard': 'third',
        # Fourth variations
        'forth': 'fourth', 'fouth': 'fourth', '4th': 'fourth', 'fourth': 'fourth',
        'foreth': 'fourth', 'forf': 'fourth',
        # Fifth variations
        'fith': 'fifth', 'fif': 'fifth', '5th': 'fifth', 'fifith': 'fifth',
        # Sixth variations
        'sith': 'sixth', 'sikth': 'sixth', '6th': 'sixth', 'sixht': 'sixth',
        # Seventh variations
        'sevnth': 'seventh', 'sevanth': 'seventh', '7th': 'seventh',
        # Eighth variations
        'eith': 'eighth', 'aith': 'eighth', '8th': 'eighth', 'eight': 'eighth',
        # Ninth variations
        'nineth': 'ninth', 'nith': 'ninth', '9th': 'ninth', 'naineth': 'ninth',
        # Tenth variations
        'tinth': 'tenth', 'tanth': 'tenth', '10th': 'tenth', 'tent': 'tenth',
    }

    # ============================================================
    # EDGE CASE: Exam Type Mishearings (for noisy environments)
    # ============================================================
    EXAM_TYPE_MISHEARINGS = {
        # Midterm variations
        'mid term': 'midterm', 'mid-term': 'midterm', 'mid tum': 'midterm',
        'midtown': 'midterm', 'mid tarm': 'midterm', 'mit term': 'midterm',
        'mid turm': 'midterm', 'medium': 'midterm', 'mid tam': 'midterm',
        'mid time': 'midterm', 'midterms': 'midterm', 'mid terms': 'midterm',
        'middterm': 'midterm', 'mit tarm': 'midterm', 'mid exam': 'midterm',
        # Final variations
        'finally': 'final', 'finale': 'final', 'vinyl': 'final', 'finel': 'final',
        'fnal': 'final', 'fainal': 'final', 'final term': 'final',
        'finalterm': 'final', 'finel term': 'final', 'finals': 'final',
        'final exam': 'final', 'fanal': 'final', 'finall': 'final',
        # Unit test variations
        'unit test': 'unittest', 'unit taste': 'unittest', 'you need test': 'unittest',
        'unit tast': 'unittest', 'unit text': 'unittest', 'unit best': 'unittest',
        'unite test': 'unittest', 'unit tests': 'unittest', 'unittests': 'unittest',
        'unit tist': 'unittest', 'yunit test': 'unittest', 'unit': 'unittest',
    }

    # ============================================================
    # EDGE CASE: Indian English Accent Variations
    # Common pronunciation patterns in Indian English
    # ============================================================
    ACCENT_VARIATIONS = {
        # Roll/Student variations
        'role': 'roll', 'rule': 'roll', 'rool': 'roll', 'rol': 'roll',
        'rowl': 'roll', 'roul': 'roll',
        'stoodent': 'student', 'stooden': 'student', 'studant': 'student',

        # Update/Marks variations
        'ap date': 'update', 'updet': 'update', 'apdate': 'update',
        'marxs': 'marks', 'max': 'marks', 'march': 'marks', 'mark s': 'marks',

        # Question variations
        'kestion': 'question', 'kwestion': 'question', 'queston': 'question',
        'questionwise': 'question wise', 'question vise': 'question wise',

        # Give/Enter variations
        'geev': 'give', 'giv': 'give', 'gif': 'give',
        'entar': 'enter', 'antar': 'enter',

        # Open/Navigate variations
        'oopen': 'open', 'opan': 'open',
        'naviaget': 'navigate', 'naviget': 'navigate',

        # Attendance variations
        'attendence': 'attendance', 'attandance': 'attendance',
        'attendens': 'attendance', 'atendance': 'attendance',

        # Report variations
        'repart': 'report', 'repot': 'report',

        # Class variations
        'claas': 'class', 'clas': 'class', 'klass': 'class',

        # Present/Absent variations
        'prasent': 'present', 'presant': 'present',
        'absant': 'absent', 'absen': 'absent',

        # "Mark all" mishearings (common Indian English STT errors)
        'mahakal': 'mark all', 'maha kal': 'mark all', 'mahaall': 'mark all',
        'markall': 'mark all', 'marcal': 'mark all', 'markal': 'mark all',

        # Fee/Show variations (common Whisper mishearings)
        'should fee': 'show fee', 'should be': 'show fee',
        'should free': 'show fee', 'should fees': 'show fees',
        'so fee': 'show fee', 'so fees': 'show fees',
        'so free': 'show fee',

        # Fee-related
        'fees': 'fees', 'feed': 'fee',
        'detales': 'details', 'detals': 'details',
        'defectors': 'defaulters', 'deflectors': 'defaulters',
        'colection': 'collection', 'collation': 'collection',
        'received': 'receipt', 'recieved': 'receipt', 'recept': 'receipt',
        'reciept': 'receipt', 'recipt': 'receipt',
    }

    # ============================================================
    # EDGE CASE HANDLING: Section 3 - Number Confusion
    # ============================================================
    # Teen vs Ty disambiguation (handled in context)
    TEEN_TY_WORDS = {
        'thirteen': 13, 'thirty': 30,
        'fourteen': 14, 'forty': 40,
        'fifteen': 15, 'fifty': 50,
        'sixteen': 16, 'sixty': 60,
        'seventeen': 17, 'seventy': 70,
        'eighteen': 18, 'eighty': 80,
        'nineteen': 19, 'ninety': 90,
    }

    # Hindi numbers (comprehensive with STT variations)
    HINDI_NUMBERS = {
        # 1-10 with variations
        'ek': '1', 'aik': '1', 'ik': '1', 'eck': '1', 'ak': '1',
        'do': '2', 'doo': '2', 'doe': '2', 'du': '2',
        'teen': '3', 'tin': '3', 'tein': '3', 'tiin': '3',
        'chaar': '4', 'char': '4', 'chaaar': '4', 'car': '4',
        'paanch': '5', 'paach': '5', 'panch': '5', 'punch': '5', 'paunch': '5',
        'chhe': '6', 'che': '6', 'chhey': '6', 'chey': '6', 'shay': '6',
        'saat': '7', 'sat': '7', 'saath': '7', 'sath': '7',
        'aath': '8', 'ath': '8', 'aatt': '8', 'aat': '8',
        'nau': '9', 'now': '9', 'naw': '9', 'no': '9',
        'das': '10', 'dus': '10', 'duss': '10', 'thus': '10',

        # 11-20
        'gyarah': '11', 'gyara': '11', 'gyaarah': '11', 'giyarah': '11',
        'barah': '12', 'bara': '12', 'baarah': '12', 'barha': '12',
        'terah': '13', 'tera': '13', 'terha': '13', 'teerha': '13',
        'chaudah': '14', 'chauda': '14', 'choda': '14', 'chaudha': '14',
        'pandrah': '15', 'pandra': '15', 'pundra': '15', 'pandara': '15',
        'solah': '16', 'sola': '16', 'solha': '16', 'solaa': '16',
        'satrah': '17', 'satra': '17', 'satrha': '17', 'satara': '17',
        'atharah': '18', 'athara': '18', 'athaarha': '18', 'aathra': '18',
        'unnis': '19', 'unees': '19', 'unnees': '19', 'unis': '19',
        'bees': '20', 'bis': '20', 'biss': '20', 'beees': '20',

        # 21-30 (common)
        'ikkis': '21', 'ikees': '21',
        'bais': '22', 'baees': '22',
        'teis': '23', 'teees': '23',
        'chaubis': '24', 'chobees': '24',
        'pachis': '25', 'pacheees': '25',
        'chhabbis': '26', 'chabbees': '26',
        'sattais': '27', 'sataees': '27',
        'attais': '28', 'atthaees': '28',
        'untis': '29', 'untees': '29',
        'tees': '30', 'tis': '30',

        # Tens
        'chalis': '40', 'chaalis': '40',
        'pachas': '50', 'pachaas': '50',
        'saath': '60', 'sath': '60',
        'sattar': '70', 'sattur': '70',
        'assi': '80', 'asee': '80',
        'nabbe': '90', 'nabbey': '90',
        'sau': '100', 'so': '100', 'soo': '100',
    }

    # Common Hindi-English mixed phrases
    HINDI_ENGLISH_PHRASES = {
        'roll number ek': 'roll number 1',
        'student ek': 'student 1',
        'roll ek': 'roll 1',
        'class ek': 'class 1',
        'section a': 'section a',
        'marks do': 'marks 2',
        'question ek': 'question 1',
    }

    # ============================================================
    # SECTION 7: Keyword-Based Fallback for Noisy Environments
    # When pattern matching fails, use keyword combinations
    # ============================================================
    KEYWORD_FALLBACK = {
        'CANCEL': {
            # Cancel/Stop/Undo commands
            'required_any': [['cancel', 'stop', 'undo', 'abort', 'nevermind', 'dismiss', 'close', 'nahi', 'ruko']],
            'boost': ['that', 'this', 'it', 'command', 'back'],
            'min_confidence': 0.3,  # Low threshold - if user says cancel, respect it
        },
        'NAVIGATE_REPORTS': {
            # Must have at least one keyword from each group
            'required_any': [['report', 'reports', 'analytics', 'analytic']],
            # Optional boost keywords
            'boost': ['open', 'show', 'go', 'view', 'navigate'],
            'min_confidence': 0.3,  # Lower for navigation (single keyword should work)
        },
        'NAVIGATE_DASHBOARD': {
            'required_any': [['dashboard', 'home']],
            'boost': ['open', 'go', 'show', 'back', 'main'],
            'min_confidence': 0.3,  # Lower for navigation
        },
        'NAVIGATE_MARKS': {
            'required_any': [['marks', 'mark', 'marksheet']],
            'exclude': ['update', 'enter', 'give', 'question', 'report', 'download'],  # These are action commands
            'boost': ['open', 'go', 'show', 'view'],
            'min_confidence': 0.3,
        },
        'NAVIGATE_ATTENDANCE': {
            'required_any': [['attendance']],
            'exclude': ['mark', 'update', 'present', 'absent'],  # These are action commands
            'boost': ['open', 'go', 'show', 'view'],
            'min_confidence': 0.3,
        },
        'UPDATE_MARKS': {
            'required_any': [['roll', 'student', 'rule']],
            'required_all': [],  # Need numbers, checked separately
            'boost': ['marks', 'mark', 'update', 'enter', 'give', 'maths', 'hindi', 'english', 'science', 'social'],
            'min_confidence': 0.5,  # Higher for action commands
        },
        'DOWNLOAD_PROGRESS_REPORT': {
            'required_any': [['download', 'export', 'generate', 'print'], ['report', 'progress']],
            'boost': ['student', 'roll', 'card'],
            'min_confidence': 0.5,
        },
        'COLLECT_FEE': {
            'required_any': [['collect', 'take', 'receive', 'accept', 'lelo', 'lo', 'jaama', 'jama', 'nikalo', 'pay', 'paying', 'deposit', 'submit', 'process', 'bharo', 'bharwa', 'dena', 'lena']],
            'boost': ['fee', 'fees', 'payment', 'paisa', 'rupees', 'cash', 'roll', 'student', 'upi', 'card', 'cheque', 'tuition', 'transport', 'bus', 'half', 'partial'],
            'exclude': ['report', 'defaulter', 'today', 'open', 'show', 'view', 'page', 'list'],
            'min_confidence': 0.4,
        },
        'OPEN_FEE_PAGE': {
            'required_any': [['fee', 'fees', 'collection', 'collections']],
            'exclude': ['collect', 'take', 'receive', 'defaulter', 'defaulters', 'today', 'report', 'reports',
                        'analytics', 'analysis', 'summary', 'statistics', 'stats', 'breakdown', 'trend', 'dashboard',
                        'lelo', 'lo', 'nikalo'],
            'boost': ['open', 'show', 'go', 'view', 'see', 'page', 'list', 'payment', 'kholo', 'dikhao'],
            'min_confidence': 0.3,
        },
        'TODAY_COLLECTION': {
            'required_any': [['today', 'aaj', 'far', 'now'], ['collection', 'collected', 'total', 'kitna', 'kitni', 'paisa']],
            'boost': ['show', 'how', 'much', 'fee', 'check', 'tell', 'batao', 'so', 'till'],
            'min_confidence': 0.5,
        },
        'SHOW_DEFAULTERS': {
            'required_any': [['defaulter', 'defaulters', 'unpaid', 'overdue', 'baki', 'baaki', 'outstanding', 'arrears', 'pending']],
            'boost': ['show', 'list', 'view', 'fee', 'class', 'wale', 'students', 'nahi'],
            'min_confidence': 0.3,
        },
        'NAVIGATE_FEE_REPORTS': {
            'required_any': [['fee', 'fees', 'collection'], ['report', 'reports', 'analytics', 'analysis', 'summary', 'stats', 'statistics', 'dashboard', 'trend', 'breakdown', 'distribution']],
            'boost': ['open', 'show', 'go', 'view', 'monthly', 'weekly', 'yearly'],
            'min_confidence': 0.5,
        },
    }

    # ============================================================
    # SECTION 4: Mid-Sentence Correction Keywords
    # These indicate the speaker is correcting themselves
    # ============================================================
    CORRECTION_KEYWORDS = [
        # Full corrections (discard everything before)
        r'\bsorry\b',
        r'\bno\s+wait\b',
        r'\bwait\s+no\b',
        r'\bactually\b',
        r'\bi\s+mean\b',
        r'\bi\s+meant\b',
        r'\bnot\s+that\b',
        r'\bcorrection\b',
        # NOTE: "instead" removed - handled separately as "X instead of Y" pattern
        r'\bhold\s+on\b',
        r'\bscratch\s+that\b',
        r'\bignore\s+that\b',
        r'\bforget\s+that\b',
        r'\bforget\s+it\b',
        r'\bmy\s+bad\b',
        r'\blet\s+me\s+correct\b',
        r'\bwrong\b',
        r'\bmistake\b',
        # Hindi corrections
        r'\bgalat\b',  # "wrong" in Hindi
        r'\bnahi\s+nahi\b',  # "no no" in Hindi
        r'\bruko\b',  # "wait" in Hindi
    ]

    # Keywords that indicate "change X to Y" pattern
    CHANGE_TO_KEYWORDS = [
        r'change\s+(?:that\s+)?to',
        r'make\s+(?:that\s+|it\s+)?',
        r'should\s+be',
        r'meant\s+to\s+say',
    ]

    # ============================================================
    # SECTION 8: Repetition & Stuttering - Words to deduplicate
    # ============================================================
    # Common filler words to remove
    FILLER_WORDS = [
        # English fillers
        r'\buh\b', r'\bum\b', r'\ber\b', r'\bah\b', r'\bhmm\b',
        r'\blet\s+me\s+see\b', r'\bokay\s+so\b', r'\bwell\b',
        r'\blike\b', r'\byou\s+know\b', r'\bbasically\b',
        r'\bactually\s+', r'\bso\s+basically\b', r'\bjust\s+',

        # Hindi/Indian English fillers
        r'\byaar\b', r'\bji\b', r'\bna\b', r'\bhai\s+na\b',
        r'\bmeans\b', r'\bthat\s+means\b', r'\bi\s+mean\s+',
        r'\bthik\s+hai\b', r'\bachha\b', r'\bhaan\b',
        r'\bwoh\b', r'\bwo\b', r'\bkya\b',

        # Thinking aloud
        r'\bwait\s+wait\b', r'\bhold\s+on\b', r'\bone\s+second\b',
        r'\blet\s+me\s+think\b', r'\bi\s+think\b',
    ]

    # Maximum command length (characters) - longer commands may be truncated or noisy
    MAX_COMMAND_LENGTH = 500

    # Command verbs that indicate a complete new command
    COMMAND_VERBS = [
        r'\bupdate\b', r'\bchange\b', r'\bset\b', r'\bmark\b', r'\benter\b',
        r'\bopen\b', r'\bshow\b', r'\bgo\b', r'\bnavigate\b', r'\bdisplay\b',
        r'\bdownload\b', r'\bgenerate\b', r'\bview\b', r'\bget\b',
        r'\bcollect\b', r'\bcheck\b', r'\bdeposit\b', r'\bpay\b', r'\btake\b',
        r'\blist\b', r'\bprocess\b', r'\baccept\b', r'\breceive\b',
    ]

    @classmethod
    def _has_command_verb(cls, text):
        """Check if text contains a command verb indicating a complete command."""
        for verb_pattern in cls.COMMAND_VERBS:
            if re.search(verb_pattern, text, re.IGNORECASE):
                return True
        return False

    @classmethod
    def _handle_mid_sentence_corrections(cls, text):
        """
        Handle mid-sentence corrections where speaker corrects themselves.

        Section 4 Edge Case Implementation.

        Examples:
        - "Update maths marks... no wait, science marks 90" → "science marks 90"
        - "Roll 5 gets 80... sorry, roll 6 gets 80" → "roll 6 gets 80"
        - "Mathematics 100... actually make it 90" → "make it 90"
        - "Question 3 is 8... I mean question 4 is 8" → "question 4 is 8"

        But NOT for value corrections that don't contain a new command:
        - "update marks for student 1 maths 100 hindi 90 sorry in maths I meant 95"
          → Keep original, apply correction to maths value

        Args:
            text: The input text to process

        Returns:
            str: Text with corrections applied (only the corrected part)
        """
        original_text = text

        # Strategy 1: Find correction keywords and take only what comes after
        # BUT only if the correction contains a complete new command
        for pattern in cls.CORRECTION_KEYWORDS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                # Take only the part after the correction keyword
                after_correction = text[match.end():].strip()
                # Remove any leading punctuation or filler
                after_correction = re.sub(r'^[\s,\.\-:;]+', '', after_correction)

                if after_correction:
                    # Check if the correction contains a command verb or meaningful entity keywords
                    # If it does, this is a new command - discard the old one
                    # If not, this is a value correction - try to merge
                    has_entity_keywords = bool(re.search(
                        r'\b(?:fee|fees|details?|student|roll|rule|class|marks?|attendance|collection|defaulter|report)\b',
                        after_correction, re.IGNORECASE
                    ))
                    if cls._has_command_verb(after_correction) or has_entity_keywords:
                        logger.info(f"[CORRECTION] Found '{match.group()}' with new command/entity - discarding before, keeping: '{after_correction}'")
                        text = after_correction
                        # Continue checking for more corrections (nested corrections)
                    else:
                        # This is a value correction like "sorry in maths I meant 95"
                        # Try to extract the corrected value and subject
                        logger.info(f"[CORRECTION] Found '{match.group()}' but no new command - treating as value correction")

                        # Check for pattern: "in [subject] ... [number]" or "[subject] ... [number]"
                        # Extract the subject and new value
                        value_correction = cls._extract_value_correction(after_correction)
                        if value_correction:
                            subject, new_value = value_correction
                            # Get the part before the correction
                            before_correction = text[:match.start()].strip()
                            # Apply the correction by replacing the value for that subject
                            corrected = cls._apply_value_correction(before_correction, subject, new_value)
                            if corrected != before_correction:
                                logger.info(f"[CORRECTION] Applied value correction: {subject} → {new_value}")
                                text = corrected
                            else:
                                # Couldn't apply correction, keep original text before correction
                                logger.info(f"[CORRECTION] Could not apply value correction, keeping original before correction")
                                text = before_correction
                        else:
                            # Couldn't extract correction, keep original text before correction
                            logger.info(f"[CORRECTION] Could not extract value correction, keeping original before correction")
                            text = text[:match.start()].strip()

        # Strategy 2: Handle "change X to Y" patterns
        # "change that to 90" → extract the new value
        for pattern in cls.CHANGE_TO_KEYWORDS:
            match = re.search(pattern + r'\s+(.+)', text, re.IGNORECASE)
            if match:
                new_value = match.group(1).strip()
                # Keep some context before the "change to" if it contains subject/roll info
                before_match = text[:match.start()].strip()

                # Check if before contains important context (roll number, subject, question)
                has_context = re.search(r'(roll|student|question|maths?|hindi|english|science|social|computer)', before_match, re.IGNORECASE)

                if has_context:
                    # Keep the context but replace the value
                    # "roll 5 maths 80 change that to 90" → "roll 5 maths 90"
                    # This is complex, so just log and let entity extraction handle it
                    logger.info(f"[CORRECTION] Found 'change to' with context - keeping full text for entity extraction")
                else:
                    # No important context, just use the new value
                    logger.info(f"[CORRECTION] Found 'change to' pattern - new value: '{new_value}'")
                    # Don't modify text here, let entity extraction pick up the last value

        # Strategy 3: Handle "instead of X give Y" patterns for specific subjects
        # "in mathematics instead of 92 give 97" → apply correction to mathematics
        # This handles cases where there's no correction keyword but has "instead of"
        subject_pattern = r'(maths?|mathematics|hindi|english|science|social(?:\s*studies)?|computer)'
        instead_pattern = rf'(?:in\s+|for\s+)?{subject_pattern}\s+instead\s+of\s+(\d+)\s+(?:give|put|use|make\s+it|set)\s+(\d+)'

        match = re.search(instead_pattern, text, re.IGNORECASE)
        if match:
            subject = match.group(1).lower()
            old_value = match.group(2)
            new_value = match.group(3)

            logger.info(f"[CORRECTION] Strategy 3: Found 'instead of' pattern for {subject}: {old_value} → {new_value}")

            # Get the part before "in [subject] instead of..."
            before_correction = text[:match.start()].strip()

            # Apply the correction
            corrected = cls._apply_value_correction(before_correction, subject, new_value)

            if corrected != before_correction:
                logger.info(f"[CORRECTION] Strategy 3 applied: {subject} changed to {new_value}")
                text = corrected
            else:
                # If we couldn't apply to existing text, just use the text before correction
                text = before_correction
                logger.info(f"[CORRECTION] Strategy 3: Keeping text before correction")

        # Strategy 4: Handle repeated values - use the last one
        # "roll 5... roll 6" - the second roll is likely the correction
        # This is handled in entity extraction by taking the last match

        if text != original_text:
            logger.info(f"[CORRECTION] Final result: '{original_text}' → '{text}'")

        return text

    @classmethod
    def _extract_value_correction(cls, correction_text):
        """
        Extract subject and new value from a value correction phrase.

        Examples:
        - "I am given mathematics as 97 instead of 92" → ("mathematics", "92") [want 92, not 97]
        - "in mathematics I am given hundred instead of 92" → ("mathematics", "100")
        - "maths 90 instead of 92" → ("maths", "90")
        - "yaar in maths it should be 95" → ("maths", "95")
        - "maths should be 100" → ("maths", "100")

        Returns:
            tuple(subject, new_value) or None if cannot extract
        """
        # Subject patterns
        subject_pattern = r'(maths?|mathematics|hindi|english|science|social(?:\s*studies)?|computer)'

        # Convert word numbers helper
        word_to_num = {
            'hundred': '100', 'ninety': '90', 'eighty': '80', 'seventy': '70',
            'sixty': '60', 'fifty': '50', 'forty': '40', 'thirty': '30',
            'twenty': '20', 'ten': '10'
        }

        number_pattern = r'(\d+|hundred|ninety|eighty|seventy|sixty|fifty|forty|thirty|twenty|ten)'

        # Pattern 0: "I am given [subject] as [wrong_value] instead of [correct_value]"
        # Example: "I am given mathematics as 97 instead of 92" → want 92 (the correct one)
        # Also handles: "that I am given..." or "yaar I make a mistake that I am given..."
        match = re.search(
            rf'(?:i\s+(?:am\s+)?(?:given|said|meant)|gave|i\s+(?:make\s+a\s+)?mistake.*?i\s+(?:am\s+)?(?:given|said))\s+{subject_pattern}\s+(?:as\s+)?{number_pattern}\s+instead\s+of\s+{number_pattern}',
            correction_text,
            re.IGNORECASE
        )
        if match:
            subject = match.group(1).lower()
            wrong_value = match.group(2).lower()
            correct_value = match.group(3).lower()
            # In "given X as 97 instead of 92", the user WANTS 92, not 97
            if correct_value in word_to_num:
                correct_value = word_to_num[correct_value]
            logger.info(f"[CORRECTION] Pattern 0 matched: {subject} = {correct_value} (was wrongly {wrong_value})")
            return (subject, correct_value)

        # Pattern 1a: "in [subject] instead of [old] give [new]" - use new value
        # Example: "in mathematics instead of 92 give 97" → maths should be 97
        match = re.search(
            rf'(?:in\s+|for\s+)?{subject_pattern}\s+instead\s+of\s+{number_pattern}\s+(?:give|put|use|make\s+it|set)\s+{number_pattern}',
            correction_text,
            re.IGNORECASE
        )
        if match:
            subject = match.group(1).lower()
            old_value = match.group(2).lower()
            new_value = match.group(3).lower()
            if new_value in word_to_num:
                new_value = word_to_num[new_value]
            logger.info(f"[CORRECTION] Pattern 1a matched: {subject} = {new_value} (replacing {old_value})")
            return (subject, new_value)

        # Pattern 1b: "[subject] instead of [old] give [new]" - use new value
        # Example: "mathematics instead of 92 give 97" → maths should be 97
        match = re.search(
            rf'{subject_pattern}\s+instead\s+of\s+{number_pattern}\s+(?:give|put|use|make\s+it|set)\s+{number_pattern}',
            correction_text,
            re.IGNORECASE
        )
        if match:
            subject = match.group(1).lower()
            old_value = match.group(2).lower()
            new_value = match.group(3).lower()
            if new_value in word_to_num:
                new_value = word_to_num[new_value]
            logger.info(f"[CORRECTION] Pattern 1b matched: {subject} = {new_value} (replacing {old_value})")
            return (subject, new_value)

        # Pattern 1: "[subject] [number] instead of [number]" - X instead of Y means use X
        # Example: "maths 90 instead of 92" → maths should be 90
        match = re.search(
            rf'{subject_pattern}\s+(?:as\s+)?{number_pattern}\s+instead\s+of\s+{number_pattern}',
            correction_text,
            re.IGNORECASE
        )
        if match:
            subject = match.group(1).lower()
            new_value = match.group(2).lower()
            if new_value in word_to_num:
                new_value = word_to_num[new_value]
            logger.info(f"[CORRECTION] Pattern 1 matched: {subject} = {new_value} (instead of {match.group(3)})")
            return (subject, new_value)

        # Pattern 2: "[subject] should be [number]" or "it should be [number]" with subject context
        match = re.search(
            rf'{subject_pattern}\s+(?:should\s+be|is|was|to)\s+{number_pattern}',
            correction_text,
            re.IGNORECASE
        )
        if match:
            subject = match.group(1).lower()
            new_value = match.group(2).lower()
            if new_value in word_to_num:
                new_value = word_to_num[new_value]
            logger.info(f"[CORRECTION] Pattern 2 matched: {subject} = {new_value}")
            return (subject, new_value)

        # Pattern 3: "in [subject] ... [number]" - general pattern
        match = re.search(
            rf'(?:in\s+|for\s+)?{subject_pattern}.*?(?:should\s+be|i\s+(?:am\s+)?(?:given|meant?|said)|is|it\'?s?|as|give)\s+{number_pattern}',
            correction_text,
            re.IGNORECASE
        )
        if match:
            subject = match.group(1).lower()
            new_value = match.group(2).lower()
            if new_value in word_to_num:
                new_value = word_to_num[new_value]
            logger.info(f"[CORRECTION] Pattern 3 matched: {subject} = {new_value}")
            return (subject, new_value)

        # Pattern 4: Look for "instead of [number]" and find subject + number before it
        # Example: "that I am given mathematics as 97 instead of 92"
        match = re.search(
            rf'{subject_pattern}.*?{number_pattern}\s+instead\s+of\s+{number_pattern}',
            correction_text,
            re.IGNORECASE
        )
        if match:
            subject = match.group(1).lower()
            # In this pattern, we have "subject ... X instead of Y"
            # Usually means user said X but wants Y
            given_value = match.group(2).lower()
            wanted_value = match.group(3).lower()
            if wanted_value in word_to_num:
                wanted_value = word_to_num[wanted_value]
            logger.info(f"[CORRECTION] Pattern 4 matched: {subject} = {wanted_value} (was wrongly {given_value})")
            return (subject, wanted_value)

        return None

    @classmethod
    def _apply_value_correction(cls, text, subject, new_value):
        """
        Apply a value correction to the original text.

        Replaces the value for the specified subject with the new value.

        Example:
        - text: "update marks for student 1 maths 92 hindi 100"
        - subject: "maths", new_value: "100"
        - result: "update marks for student 1 maths 100 hindi 100"
        """
        # Normalize subject name
        subject_variations = {
            'mathematics': 'maths?|mathematics',
            'maths': 'maths?|mathematics',
            'math': 'maths?|mathematics',
        }
        subject_pattern = subject_variations.get(subject, re.escape(subject))

        # Pattern to find subject followed by a number
        pattern = rf'({subject_pattern})\s+(\d+(?:\.\d+)?)'

        def replace_value(match):
            return f"{match.group(1)} {new_value}"

        result = re.sub(pattern, replace_value, text, flags=re.IGNORECASE)
        return result

    @classmethod
    def _deduplicate_repetitions(cls, text):
        """
        Handle repetition and stuttering in speech.

        Section 8 Edge Case Implementation.

        Handles:
        - Consecutive duplicate words: "roll 5, roll 5" → "roll 5"
        - Duplicate command words: "update update marks" → "update marks"
        - Self-echo numbers: "ninety ninety" → "ninety" (before conversion)
        - Filler words: "uh", "um", "let me see" → removed

        Args:
            text: Input text to process

        Returns:
            str: Text with repetitions removed
        """
        original_text = text

        # Step 1: Remove filler words
        for pattern in cls.FILLER_WORDS:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)

        # Step 2: Remove consecutive duplicate words
        # "roll 5 roll 5" → "roll 5"
        # "update update marks" → "update marks"
        # Uses regex to find word repeated immediately after itself (with optional comma/space)
        text = re.sub(r'\b(\w+)[\s,]+\1\b', r'\1', text, flags=re.IGNORECASE)

        # Step 3: Remove consecutive duplicate phrases (2-3 words)
        # "roll 5, roll 5" → "roll 5"
        # "maths 90 maths 90" → "maths 90"
        text = re.sub(r'\b(\w+\s+\w+)[\s,]+\1\b', r'\1', text, flags=re.IGNORECASE)
        text = re.sub(r'\b(\w+\s+\w+\s+\w+)[\s,]+\1\b', r'\1', text, flags=re.IGNORECASE)

        # Step 4: Handle "thinking aloud" patterns
        # "let me see roll 5 yes roll 5" → "roll 5"
        text = re.sub(r'\blet\s+me\s+(?:see|think)\b[,\s]*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\b(?:yes|yeah|okay|ok)\s+', '', text, flags=re.IGNORECASE)

        # Cleanup extra spaces and commas
        text = re.sub(r',\s*,+', ',', text)
        text = re.sub(r'\s+', ' ', text).strip()
        text = re.sub(r'^[,\s]+|[,\s]+$', '', text)  # Remove leading/trailing commas

        # Step 4b: Handle repeated command prefixes (speaker restarts command)
        # "go to 8 go to class 8" → "go to class 8"
        # "open 5th open class 5" → "open class 5"
        # "show fees show fee details" → "show fee details"
        command_prefixes = [
            r'go\s+to', r'open', r'show', r'view', r'display',
            r'update', r'change', r'set', r'mark', r'collect',
            r'check', r'get',
        ]
        for prefix in command_prefixes:
            matches = list(re.finditer(prefix, text, re.IGNORECASE))
            if len(matches) >= 2:
                # Check if this is a batch command (multiple students/rolls with different data)
                # If text between occurrences contains different roll/student numbers, it's batch - don't dedup
                first_end = matches[0].end()
                last_start = matches[-1].start()
                between = text[first_end:last_start]
                roll_numbers = re.findall(r'(?:student|roll|rule)\s+(\d+)', between + text[last_start:], re.IGNORECASE)
                if len(set(roll_numbers)) >= 2:
                    logger.info(f"[DEDUP] Skipping dedup for '{prefix}' - batch command with multiple students: {roll_numbers}")
                    continue

                # Keep from the last occurrence (speaker's final/corrected version)
                last_match = matches[-1]
                new_text = text[last_match.start():].strip()
                if new_text:
                    logger.info(f"[DEDUP] Repeated command prefix '{prefix}': '{text}' → '{new_text}'")
                    text = new_text
                break  # Only process the first matching prefix

        # Step 5: Run deduplication again in case removing fillers created new duplicates
        # Keep running until no more changes
        prev = None
        iterations = 0
        while prev != text and iterations < 5:
            prev = text
            iterations += 1
            # Deduplicate single words
            text = re.sub(r'\b(\w+)[\s,]+\1\b', r'\1', text, flags=re.IGNORECASE)
            # Deduplicate two-word phrases
            text = re.sub(r'\b(\w+\s+\w+)[\s,]+\1\b', r'\1', text, flags=re.IGNORECASE)
            # Cleanup
            text = re.sub(r'\s+', ' ', text).strip()

        if text != original_text:
            logger.info(f"[DEDUP] Removed repetitions: '{original_text}' → '{text}'")

        return text

    @classmethod
    def normalize_stt_text(cls, text):
        """
        Normalize STT output by handling edge cases:

        Section 1: Homophones & Similar Sounds
        - to/too → 2, for → 4, won → 1, ate → 8
        - roll/role/rule normalization
        - marks/max normalization

        Section 2: Subject Name Mishearings
        - mass/match/moths → maths
        - indy/indie → hindi
        - signs/silence → science

        Section 3: Number Confusion
        - fifteen vs fifty disambiguation
        - Hindi numbers (ek, do, teen...)
        - Decimal handling
        """
        text_lower = text.lower().strip()

        logger.info(f"[NORM-0] Original: '{text_lower}'")

        # ============================================================
        # SECTION 9: Very Long Command Handling
        # Truncate excessively long commands that may be noisy/corrupted
        # ============================================================
        if len(text_lower) > cls.MAX_COMMAND_LENGTH:
            logger.warning(f"[NORM-TRUNCATE] Command too long ({len(text_lower)} chars), truncating to {cls.MAX_COMMAND_LENGTH}")
            # Try to find a natural break point near the limit
            truncated = text_lower[:cls.MAX_COMMAND_LENGTH]
            # Find last complete sentence or phrase
            last_break = max(
                truncated.rfind('.'),
                truncated.rfind(','),
                truncated.rfind(' '),
            )
            if last_break > cls.MAX_COMMAND_LENGTH // 2:
                text_lower = truncated[:last_break].strip()
            else:
                text_lower = truncated.strip()
            logger.info(f"[NORM-TRUNCATE] Truncated to: '{text_lower}'")

        # ============================================================
        # SECTION 4: Mid-Sentence Corrections
        # Handle cases where teacher corrects themselves while speaking
        # "Update maths... no wait, science 90" → "science 90"
        # "Roll 5 gets 80... sorry, roll 6 gets 80" → "roll 6 gets 80"
        # ============================================================
        text_lower = cls._handle_mid_sentence_corrections(text_lower)
        logger.info(f"[NORM-0-CORRECTIONS] After mid-sentence corrections: '{text_lower}'")

        # ============================================================
        # SECTION 8: Repetition & Stuttering Handling
        # Remove filler words and deduplicate repeated words/phrases
        # "roll 5, roll 5" → "roll 5", "update update marks" → "update marks"
        # ============================================================
        text_lower = cls._deduplicate_repetitions(text_lower)
        logger.info(f"[NORM-0-DEDUP] After deduplication: '{text_lower}'")

        # ============================================================
        # SECTION 10: Indian English Accent Variations
        # Handle common pronunciation patterns in Indian English
        # "stoodent" → "student", "kestion" → "question", etc.
        # ============================================================
        for accent_word, correct_word in cls.ACCENT_VARIATIONS.items():
            # Handle multi-word patterns (like "ap date" → "update")
            if ' ' in accent_word:
                text_lower = text_lower.replace(accent_word, correct_word)
            else:
                text_lower = re.sub(rf'\b{re.escape(accent_word)}\b', correct_word, text_lower)

        logger.info(f"[NORM-0-ACCENT] After accent normalization: '{text_lower}'")

        # ============================================================
        # SECTION 10a: Ordinal Mishearings (for noisy environments)
        # "fast B" → "first B", "fist A" → "first A", etc.
        # ============================================================
        for mishearing, correct in cls.ORDINAL_MISHEARINGS.items():
            if ' ' in mishearing:
                text_lower = text_lower.replace(mishearing, correct)
            else:
                text_lower = re.sub(rf'\b{re.escape(mishearing)}\b', correct, text_lower)

        logger.info(f"[NORM-0-ORDINAL] After ordinal normalization: '{text_lower}'")

        # ============================================================
        # SECTION 10b: Exam Type Mishearings (for noisy environments)
        # "mid term" → "midterm", "mid tum" → "midterm", etc.
        # ============================================================
        for mishearing, correct in cls.EXAM_TYPE_MISHEARINGS.items():
            if ' ' in mishearing:
                text_lower = text_lower.replace(mishearing, correct)
            else:
                text_lower = re.sub(rf'\b{re.escape(mishearing)}\b', correct, text_lower)

        logger.info(f"[NORM-0-EXAMTYPE] After exam type normalization: '{text_lower}'")

        # ============================================================
        # SECTION 2: Subject Name Mishearings (do first, before other processing)
        # ============================================================
        for mishearing, correct in cls.SUBJECT_MISHEARINGS.items():
            text_lower = re.sub(rf'\b{re.escape(mishearing)}\b', correct, text_lower)

        # Contextual fix: "in the <number>" is likely "hindi <number>" in marks context
        text_lower = re.sub(r'\bin the\s+(\d+)', r'hindi \1', text_lower)

        logger.info(f"[NORM-0a] After subject mishearing fix: '{text_lower}'")

        # ============================================================
        # SECTION 1: Homophones - Non-numeric word fixes
        # ============================================================
        # Fix roll/role/rule variations
        text_lower = re.sub(r'\b(role|rule|rool|rol)\b', 'roll', text_lower)

        # Fix marks/max variations
        text_lower = re.sub(r'\b(max|marx|mux)\s+(?=\d)', 'marks ', text_lower)
        text_lower = re.sub(r'\b(max|marx|mux)\b(?!\s*\d)', 'marks', text_lower)

        logger.info(f"[NORM-0b] After homophone word fix: '{text_lower}'")

        # ============================================================
        # SECTION 3: Hindi Number Support
        # ============================================================
        for hindi_word, digit in cls.HINDI_NUMBERS.items():
            # "roll ek" → "roll 1", "student do" → "student 2"
            text_lower = re.sub(rf'\b{hindi_word}\b', digit, text_lower)

        logger.info(f"[NORM-0c] After Hindi number conversion: '{text_lower}'")

        # ============================================================
        # SECTION 3: Number Word to Digit Conversion (English)
        # ============================================================
        # Extended word-to-number mapping
        extended_word_to_num = {
            'zero': '0', 'one': '1', 'two': '2', 'three': '3', 'four': '4',
            'five': '5', 'six': '6', 'seven': '7', 'eight': '8', 'nine': '9',
            'ten': '10', 'eleven': '11', 'twelve': '12',
            # Teen numbers
            'thirteen': '13', 'fourteen': '14', 'fifteen': '15',
            'sixteen': '16', 'seventeen': '17', 'eighteen': '18', 'nineteen': '19',
            # Ty numbers
            'twenty': '20', 'thirty': '30', 'forty': '40', 'fifty': '50',
            'sixty': '60', 'seventy': '70', 'eighty': '80', 'ninety': '90',
            'hundred': '100',
        }

        # Convert compound numbers: "twenty one" → "21", "fifty five" → "55"
        compound_patterns = [
            (r'\btwenty\s*one\b', '21'), (r'\btwenty\s*two\b', '22'), (r'\btwenty\s*three\b', '23'),
            (r'\btwenty\s*four\b', '24'), (r'\btwenty\s*five\b', '25'), (r'\btwenty\s*six\b', '26'),
            (r'\btwenty\s*seven\b', '27'), (r'\btwenty\s*eight\b', '28'), (r'\btwenty\s*nine\b', '29'),
            (r'\bthirty\s*one\b', '31'), (r'\bthirty\s*two\b', '32'), (r'\bthirty\s*three\b', '33'),
            (r'\bthirty\s*four\b', '34'), (r'\bthirty\s*five\b', '35'), (r'\bthirty\s*six\b', '36'),
            (r'\bthirty\s*seven\b', '37'), (r'\bthirty\s*eight\b', '38'), (r'\bthirty\s*nine\b', '39'),
            (r'\bforty\s*one\b', '41'), (r'\bforty\s*two\b', '42'), (r'\bforty\s*three\b', '43'),
            (r'\bforty\s*four\b', '44'), (r'\bforty\s*five\b', '45'), (r'\bforty\s*six\b', '46'),
            (r'\bforty\s*seven\b', '47'), (r'\bforty\s*eight\b', '48'), (r'\bforty\s*nine\b', '49'),
            (r'\bfifty\s*one\b', '51'), (r'\bfifty\s*two\b', '52'), (r'\bfifty\s*three\b', '53'),
            (r'\bfifty\s*four\b', '54'), (r'\bfifty\s*five\b', '55'), (r'\bfifty\s*six\b', '56'),
            (r'\bfifty\s*seven\b', '57'), (r'\bfifty\s*eight\b', '58'), (r'\bfifty\s*nine\b', '59'),
            (r'\bsixty\s*one\b', '61'), (r'\bsixty\s*two\b', '62'), (r'\bsixty\s*three\b', '63'),
            (r'\bsixty\s*four\b', '64'), (r'\bsixty\s*five\b', '65'), (r'\bsixty\s*six\b', '66'),
            (r'\bsixty\s*seven\b', '67'), (r'\bsixty\s*eight\b', '68'), (r'\bsixty\s*nine\b', '69'),
            (r'\bseventy\s*one\b', '71'), (r'\bseventy\s*two\b', '72'), (r'\bseventy\s*three\b', '73'),
            (r'\bseventy\s*four\b', '74'), (r'\bseventy\s*five\b', '75'), (r'\bseventy\s*six\b', '76'),
            (r'\bseventy\s*seven\b', '77'), (r'\bseventy\s*eight\b', '78'), (r'\bseventy\s*nine\b', '79'),
            (r'\beighty\s*one\b', '81'), (r'\beighty\s*two\b', '82'), (r'\beighty\s*three\b', '83'),
            (r'\beighty\s*four\b', '84'), (r'\beighty\s*five\b', '85'), (r'\beighty\s*six\b', '86'),
            (r'\beighty\s*seven\b', '87'), (r'\beighty\s*eight\b', '88'), (r'\beighty\s*nine\b', '89'),
            (r'\bninety\s*one\b', '91'), (r'\bninety\s*two\b', '92'), (r'\bninety\s*three\b', '93'),
            (r'\bninety\s*four\b', '94'), (r'\bninety\s*five\b', '95'), (r'\bninety\s*six\b', '96'),
            (r'\bninety\s*seven\b', '97'), (r'\bninety\s*eight\b', '98'), (r'\bninety\s*nine\b', '99'),
        ]

        for pattern, replacement in compound_patterns:
            text_lower = re.sub(pattern, replacement, text_lower)

        # Now convert single number words
        for word, num in extended_word_to_num.items():
            text_lower = re.sub(rf'\b{word}\b', num, text_lower)

        logger.info(f"[NORM-0d] After English number word conversion: '{text_lower}'")

        # ============================================================
        # SECTION 3: Decimal Number Support
        # ============================================================
        # "seven point five" → "7.5", "eight point five" → "8.5"
        text_lower = re.sub(r'(\d+)\s+point\s+(\d+)', r'\1.\2', text_lower)
        # "seven and a half" → "7.5"
        text_lower = re.sub(r'(\d+)\s+and\s+a\s+half\b', lambda m: f"{m.group(1)}.5", text_lower)
        # "half marks" → "0.5 marks" (standalone half)
        text_lower = re.sub(r'\bhalf\s+marks?\b', '0.5 marks', text_lower)

        logger.info(f"[NORM-0e] After decimal conversion: '{text_lower}'")

        # ============================================================
        # SECTION 1: Context-sensitive Homophone Handling (to/2, for/4)
        # ============================================================
        # "marks to 90" should stay as "marks to 90" (preposition)
        # "roll to" should become "roll 2" (number)
        # "for roll" should stay as "for roll" (preposition)
        # "question for" should become "question 4" (number - less common)

        # Pattern: "roll to" or "student to" → "roll 2" when in marks context
        # IMPORTANT: "two" sounds like "to", so in marks commands, convert "to" → "2"
        # "student to mathematics 90" → "student 2 mathematics 90" (roll number 2)
        # BUT: "go to marks" should NOT become "go 2 marks"
        # Key: Only convert when followed by subject OR number (marks context)
        text_lower = re.sub(
            r'\b(roll|student)\s+to\b(?=\s+(?:maths?|mathematics|hindi|english|science|social|computer|\d))',
            r'\1 2',
            text_lower
        )
        # Also handle "student to" at end or followed by other words (assume roll 2)
        text_lower = re.sub(
            r'\b(roll|student)\s+to\b(?!\s+(?:update\b|change\b|enter\b|the\b|a\b|an\b|for\b|of\b|go\b|open\b|show\b))',
            r'\1 2',
            text_lower
        )

        # Pattern: "give to" in marks context → "give 2"
        text_lower = re.sub(r'\bgive\s+to\b(?=\s+marks|\s*$)', 'give 2', text_lower)

        # Pattern: Number homophones after specific keywords
        # "question won" → "question 1", "roll won" → "roll 1"
        text_lower = re.sub(r'\b(question|roll|student)\s+won\b', r'\1 1', text_lower)
        text_lower = re.sub(r'\b(question|roll|student)\s+too\b', r'\1 2', text_lower)

        # "ate marks" → "8 marks", "give ate" → "give 8"
        text_lower = re.sub(r'\b(ate|eat)\s+marks?\b', '8 marks', text_lower)
        text_lower = re.sub(r'\bgive\s+(ate|eat)\b', 'give 8', text_lower)
        text_lower = re.sub(r'\bas\s+(ate|eat)\b', 'as 8', text_lower)

        # Context-sensitive "free" handling: "free" → "fee" in fee context, "free" → "3" otherwise
        # "show free details" → "show fee details", "free collection" → "fee collection"
        # BUT: "question free" → "question 3" (marks context)
        fee_context_words = ['details', 'detail', 'collection', 'collect', 'payment', 'defaulter', 'defaulters',
                             'report', 'reports', 'student', 'roll', 'show', 'open', 'pending', 'status', 'due', 'dues']
        if re.search(r'\bfree\b', text_lower):
            # Check if any fee-context word is present
            if any(w in text_lower for w in fee_context_words):
                text_lower = re.sub(r'\bfree\b', 'fee', text_lower)
            else:
                text_lower = re.sub(r'\bfree\b', '3', text_lower)

        # Fix "details are" → "details of" (Whisper mishearing)
        text_lower = re.sub(r'\bdetails\s+are\b', 'details of', text_lower)
        # Fix "details off" → "details of"
        text_lower = re.sub(r'\bdetails\s+off\b', 'details of', text_lower)

        # Strip common filler words at start: "so", "um", "uh", "like", "well"
        text_lower = re.sub(r'^(?:so|um|uh|like|well|okay|ok)\s+', '', text_lower)

        logger.info(f"[NORM-0f] After context-sensitive homophone fix: '{text_lower}'")

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

        # FIX: Convert ordinal words to numbers with suffix
        # "first" → "1st", "second" → "2nd", "third" → "3rd"
        ordinal_to_num = {
            'first': '1st', 'second': '2nd', 'third': '3rd', 'fourth': '4th',
            'fifth': '5th', 'sixth': '6th', 'seventh': '7th', 'eighth': '8th',
            'ninth': '9th', 'tenth': '10th', 'eleventh': '11th', 'twelfth': '12th'
        }
        for word, num in ordinal_to_num.items():
            text_lower = re.sub(rf'\b{word}\b', num, text_lower)

        logger.info(f"[NORM-2b] After ordinal conversion: '{text_lower}'")

        # Note: Basic word-to-number conversion already done in NORM-0d
        # Here we handle remaining edge cases for "eat/ate" and context-specific conversions

        # Special case: "eat as" or "ate as" - remove the word before "as" if it's eat/ate
        # "12345678 eat as 79" → "12345678 as 79"
        text_lower = re.sub(r'\b(eat|ate)\s+as\b', 'as', text_lower)

        # Additional context-specific number fixes
        # "question for" where "for" is likely "4"
        text_lower = re.sub(r'\bquestion\s+for\b(?=\s+(?:give|is|marks|as|\d))', 'question 4', text_lower)

        logger.info(f"[NORM-3] After additional number fixes: '{text_lower}'")

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
            prefix = match.group(1)  # "questions" or "question"
            start = int(match.group(2))
            end = int(match.group(3))

            # SMART EXPANSION: Don't expand if it looks like a marks assignment
            # "question 3 to 8" (singular + small end number) = marks assignment
            # "questions 1 to 10" (plural + large range) = range to expand

            is_plural = prefix.endswith('s')
            range_size = end - start

            # Heuristics to detect marks assignment vs range:
            # 1. Singular "question" with end number <= 10 and range <= 5 → likely marks
            # 2. Plural "questions" → likely range to expand
            # 3. Range starting from 1 → likely range to expand

            if not is_plural and end <= 10 and range_size <= 5 and start > 1:
                # "question 3 to 8" - looks like marks assignment, don't expand
                logger.info(f"[RANGE] NOT expanding '{match.group()}' - looks like marks assignment")
                return match.group(0)

            # Generate range
            if start <= end and range_size < 20:  # Sanity check
                numbers = ', '.join(str(i) for i in range(start, end + 1))
                logger.info(f"[RANGE] Expanding '{match.group()}' to '{prefix} {numbers}'")
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
    def _keyword_fallback(cls, text):
        """
        Keyword-based fallback for noisy environments.

        When pattern matching fails, try to detect intent based on
        keyword combinations found in the text.

        Args:
            text: Normalized text (lowercase)

        Returns:
            tuple: (intent, confidence) or (None, 0) if no match
        """
        words = set(re.findall(r'\b\w+\b', text.lower()))
        best_match = None
        best_confidence = 0

        for intent, config in cls.KEYWORD_FALLBACK.items():
            confidence = 0
            required_met = True

            # Check required_any: at least one keyword from each group must be present
            required_any = config.get('required_any', [])
            for group in required_any:
                if not any(kw in words for kw in group):
                    required_met = False
                    break
                else:
                    # Found at least one from this group
                    matches = sum(1 for kw in group if kw in words)
                    confidence += 0.3 * matches

            if not required_met:
                continue

            # Check exclude: if any exclude keyword is present, skip this intent
            exclude = config.get('exclude', [])
            if any(kw in words for kw in exclude):
                continue

            # Check boost keywords (increase confidence)
            boost = config.get('boost', [])
            boost_matches = sum(1 for kw in boost if kw in words)
            confidence += 0.1 * boost_matches

            # Normalize confidence to 0-1 range
            confidence = min(confidence, 1.0)

            # Check minimum confidence
            min_conf = config.get('min_confidence', 0.5)
            if confidence >= min_conf and confidence > best_confidence:
                best_match = intent
                best_confidence = confidence

        if best_match:
            logger.info(f"[KEYWORD FALLBACK] Detected intent: {best_match} with confidence: {best_confidence:.2f}")

        return best_match, best_confidence

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

        # Try pattern matching first
        for intent, patterns in cls.INTENT_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    logger.info(f"Intent detected: {intent} using pattern: {pattern}")
                    return intent

        # Pattern matching failed - try keyword-based fallback for noisy environments
        logger.info(f"[NOISY ENV] Pattern matching failed, trying keyword fallback for: '{text_lower}'")
        fallback_intent, confidence = cls._keyword_fallback(text_lower)

        if fallback_intent:
            logger.info(f"[NOISY ENV] Keyword fallback matched: {fallback_intent} (confidence: {confidence:.2f})")
            return fallback_intent

        logger.warning(f"No intent matched for text: {text}")
        return 'UNKNOWN'

    @classmethod
    def check_command_completeness(cls, text, intent):
        """
        Check if a command is complete or if it was interrupted/incomplete.

        Section 6 Edge Case Implementation.

        Detects:
        - Trailing prepositions ("for", "to", "of")
        - Missing required values (no number after "roll")
        - Incomplete command structures

        Args:
            text: The normalized text
            intent: The detected intent

        Returns:
            dict: {
                'is_complete': bool,
                'missing': list of missing elements,
                'suggestion': str hint for user
            }
        """
        text_lower = text.lower().strip()
        result = {
            'is_complete': True,
            'missing': [],
            'suggestion': None
        }

        # ============================================================
        # Check 1: Trailing prepositions (command cut off)
        # ============================================================
        trailing_prepositions = [
            r'\bfor\s*$',
            r'\bto\s*$',
            r'\bof\s*$',
            r'\bin\s*$',
            r'\bthe\s*$',
            r'\bwith\s*$',
            r'\bas\s*$',
            r'\band\s*$',
        ]

        for pattern in trailing_prepositions:
            if re.search(pattern, text_lower):
                result['is_complete'] = False
                result['missing'].append('value after preposition')
                result['suggestion'] = 'Command seems incomplete. Please complete your sentence.'
                logger.warning(f"[INCOMPLETE] Trailing preposition detected in: '{text_lower}'")
                return result

        # ============================================================
        # Check 2: Intent-specific completeness checks
        # ============================================================

        if intent == 'BATCH_UPDATE_MARKS':
            # Need: at least two student/roll mentions with subject marks
            roll_matches = re.findall(r'(?:roll|student|rule)\s*\d+', text_lower)
            has_subject_marks = bool(re.search(r'(maths?|hindi|english|science|social|computer)\s*\d+', text_lower))

            if len(roll_matches) < 2:
                result['is_complete'] = False
                result['missing'].append('at least two students')
            if not has_subject_marks:
                result['is_complete'] = False
                result['missing'].append('subject and marks')
            if not result['is_complete']:
                result['suggestion'] = f"Missing: {', '.join(result['missing'])}. Example: 'Update marks for student 1 maths 90 hindi 80 update marks for student 2 maths 85'"

        elif intent == 'UPDATE_MARKS' or intent == 'ENTER_MARKS':
            # Need: roll number + at least one subject with marks
            has_roll = bool(re.search(r'(?:roll|student|rule)\s*\d+', text_lower))
            has_subject_marks = bool(re.search(r'(maths?|hindi|english|science|social|computer)\s*\d+', text_lower))

            if not has_roll:
                result['is_complete'] = False
                result['missing'].append('roll number')

            if not has_subject_marks:
                result['is_complete'] = False
                result['missing'].append('subject and marks')

            if not result['is_complete']:
                result['suggestion'] = f"Missing: {', '.join(result['missing'])}. Example: 'Update marks for roll 1 maths 90'"

        elif intent == 'UPDATE_QUESTION_MARKS':
            # Need: question number + marks value
            has_question = bool(re.search(r'question\s*\d+', text_lower))
            has_marks = bool(re.search(r'(?:to|as|give|is)\s*\d+', text_lower)) or bool(re.search(r'\d+\s*marks?', text_lower))

            if not has_question:
                result['is_complete'] = False
                result['missing'].append('question number')

            if not has_marks:
                result['is_complete'] = False
                result['missing'].append('marks value')

            if not result['is_complete']:
                result['suggestion'] = f"Missing: {', '.join(result['missing'])}. Example: 'Question 3 to 8 marks'"

        elif intent == 'MARK_ATTENDANCE':
            # Need: class/section OR context, and either "all" or roll numbers
            has_class = bool(re.search(r'class\s*\d+', text_lower))
            has_target = bool(re.search(r'(all|everyone|roll\s*\d+|student\s*\d+)', text_lower))

            # "mark all present" is valid if context provides class
            if 'all' in text_lower or 'everyone' in text_lower:
                has_target = True

            if not has_target:
                result['is_complete'] = False
                result['missing'].append('target (all students or specific roll numbers)')
                result['suggestion'] = "Specify who to mark. Example: 'Mark all present' or 'Mark roll 5 absent'"

        elif intent == 'OPEN_MARKS_SHEET' or intent == 'OPEN_ATTENDANCE_SHEET':
            # Need: class and section
            has_class = bool(re.search(r'(?:class\s*)?\d+', text_lower))
            has_section = bool(re.search(r'[a-z](?:\s|$)', text_lower))

            if not has_class:
                result['is_complete'] = False
                result['missing'].append('class number')

            if not has_section:
                result['is_complete'] = False
                result['missing'].append('section')

            if not result['is_complete']:
                result['suggestion'] = f"Missing: {', '.join(result['missing'])}. Example: 'Open class 2C marks'"

        elif intent == 'DOWNLOAD_PROGRESS_REPORT':
            # Need: roll number (class/section can come from context)
            has_roll = bool(re.search(r'(?:roll|student|rule)\s*\d+', text_lower))

            if not has_roll:
                result['is_complete'] = False
                result['missing'].append('student roll number')
                result['suggestion'] = "Specify the student. Example: 'Download report for roll 5'"

        elif intent == 'COLLECT_FEE':
            # Need: amount + roll number (class/section can come from context)
            has_amount = bool(re.search(r'\d{2,}', text_lower))
            has_roll = bool(re.search(r'(?:roll|student|rule)\s*(?:number|no\.?|num|#)?\s*\d+', text_lower))

            if not has_amount:
                result['is_complete'] = False
                result['missing'].append('amount')

            if not has_roll:
                result['is_complete'] = False
                result['missing'].append('roll number')

            if not result['is_complete']:
                result['suggestion'] = f"Missing: {', '.join(result['missing'])}. Example: 'Collect 5000 from roll 12 class 6A cash'"

        elif intent == 'SHOW_FEE_DETAILS':
            # Need: roll number (class/section can come from context)
            has_roll = bool(re.search(r'(?:roll|student|rule)\s*(?:number|no\.?|num|#)?\s*\d+', text_lower))

            if not has_roll:
                result['is_complete'] = False
                result['missing'].append('roll number')
                result['suggestion'] = "Missing: roll number. Example: 'Show fee details of student 5'"

        # ============================================================
        # Check 3: Very short commands (likely incomplete)
        # ============================================================
        # Fee intents that are naturally short commands
        SHORT_COMMAND_INTENTS = [
            'NAVIGATE_MARKS', 'NAVIGATE_ATTENDANCE', 'NAVIGATE_DASHBOARD',
            'NAVIGATE_REPORTS', 'NAVIGATE_FEE_REPORTS',
            'TODAY_COLLECTION', 'SHOW_DEFAULTERS', 'OPEN_FEE_PAGE',
            'NAVIGATE_CLASS_REPORT', 'NAVIGATE_STUDENT_REPORT', 'NAVIGATE_ATTENDANCE_REPORT',
        ]
        word_count = len(text_lower.split())
        if word_count <= 2 and intent not in SHORT_COMMAND_INTENTS:
            # Very short command that isn't simple navigation
            if not result['is_complete']:
                # Already marked incomplete, add note about length
                pass
            elif intent != 'UNKNOWN':
                # Intent detected but very short - might be incomplete
                logger.info(f"[INCOMPLETE-CHECK] Short command ({word_count} words) with intent {intent}")

        return result


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

        if intent == 'BATCH_UPDATE_MARKS':
            return cls._extract_batch_marks_entities(text, context)
        elif intent == 'BATCH_UPDATE_QUESTION_MARKS':
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
        elif intent == 'NAVIGATE_DASHBOARD':
            return {}  # No entities needed for dashboard navigation
        elif intent == 'SELECT_EXAM_TYPE':
            return cls._extract_exam_type_entities(text, context)
        elif intent == 'DOWNLOAD_PROGRESS_REPORT':
            return cls._extract_progress_report_entities(text, context)
        elif intent == 'COLLECT_FEE':
            return cls._extract_fee_collection_entities(text, context)
        elif intent == 'SHOW_FEE_DETAILS':
            return cls._extract_fee_details_entities(text, context)
        elif intent == 'OPEN_FEE_PAGE':
            return cls._extract_fee_page_entities(text, context)
        elif intent == 'SHOW_DEFAULTERS':
            return cls._extract_defaulters_entities(text, context)
        elif intent in ('TODAY_COLLECTION', 'NAVIGATE_FEE_REPORTS'):
            return {}
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
        - "Update marks for student 1 maths 90 hindi 80" (student as alternative to roll)
        """
        if context is None:
            context = {}

        logger.info(f"Extracting marks entities from text: '{text}'")
        logger.info(f"Context: {context}")

        entities = {}

        # Extract roll number (handle "rule" as speech recognition error for "roll", allow periods)
        # Also support "student" as alternative to roll/rule
        roll_patterns = [
            r'(?:student|roll|rule)[\.\s]+(?:number|no\.?|num|#)?[\.\s]*(\d+)',
            r'(?:student|roll|rule)[\.\s]+(\d+)',
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
    def _extract_batch_marks_entities(cls, text, context=None):
        """
        Extract entities for batch marks update (multiple students in one command).

        Splits text by student segments and extracts marks for each student.
        Example: "update marks for student 3 maths 100 hindi 92 update marks for student 4 hindi 928 english 94"
        """
        if context is None:
            context = {}

        logger.info(f"Extracting BATCH marks entities from text: '{text}'")

        # Split text into per-student segments
        # Pattern: split on "update/enter/add/set/change marks" or "student/roll" boundaries
        split_pattern = r'(?:update|enter|add|set|change)[\.\s]+(?:the\s+)?marks?[\.\s]+(?:for\s+|of\s+|to\s+)?'
        segments = re.split(split_pattern, text, flags=re.IGNORECASE)
        segments = [s.strip() for s in segments if s and s.strip()]

        # If splitting by "update marks" didn't work well, try splitting by "student/roll" keywords
        if len(segments) < 2:
            # Try splitting on second occurrence of student/roll
            student_pattern = r'(?=(?:student|roll|rule)[\.\s]+(?:number\s+|no\.?\s+|#)?\d+)'
            segments = re.split(student_pattern, text, flags=re.IGNORECASE)
            segments = [s.strip() for s in segments if s and s.strip()]

        logger.info(f"Split into {len(segments)} segments: {segments}")

        students = []
        for segment in segments:
            # Extract roll number from this segment
            roll_match = re.search(
                r'(?:student|roll|rule)[\.\s]+(?:number\s+|no\.?\s+|#)?\s*(\d+)',
                segment, re.IGNORECASE
            )
            if not roll_match:
                continue

            roll_number = int(roll_match.group(1))
            marks = cls._extract_subject_marks(segment)

            if marks:
                student_entity = {
                    'roll_number': roll_number,
                    'marks': marks,
                }
                # Use class/section from context
                if 'class' in context:
                    student_entity['class'] = context['class']
                if 'section' in context:
                    student_entity['section'] = context['section']

                # Also try extracting class/section from text
                class_match = re.search(r'class\s+(\d+)', segment, re.IGNORECASE)
                section_match = re.search(r'(?:class\s+\d+\s*([A-Za-z])|section\s+([A-Za-z]))', segment, re.IGNORECASE)
                if class_match:
                    student_entity['class'] = int(class_match.group(1))
                if section_match:
                    student_entity['section'] = (section_match.group(1) or section_match.group(2)).upper()

                students.append(student_entity)

        # Fallback: use context class/section for all students
        for s in students:
            if 'class' not in s and 'class' in context:
                s['class'] = context['class']
            if 'section' not in s and 'section' in context:
                s['section'] = context['section']

        logger.info(f"Extracted batch marks for {len(students)} students: {students}")
        return {'students': students}

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

        # Extract roll number (also support "student" as alternative)
        roll_patterns = [
            r'(?:for\s+|of\s+)?(?:student|roll|rule)[\.\s]+(?:number|no\.?|num|#)?[\.\s]*(\d+)',
            r'(?:student|roll|rule)[\.\s]+(\d+)',
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
                # SECTION 14: Batch Validation - List Length Mismatch
                # Instead of returning error, pair what we can and mark missing ones
                logger.warning(f"Parallel lists length mismatch: {len(question_nums)} questions vs {len(marks_nums)} marks")

                # Pair as many as we can
                paired_count = min(len(question_nums), len(marks_nums))
                for i in range(paired_count):
                    updates.append({
                        'question_number': question_nums[i],
                        'marks_obtained': marks_nums[i]
                    })

                # Track which questions are missing marks
                missing_questions = []
                if len(question_nums) > len(marks_nums):
                    # More questions than marks - some questions missing marks
                    missing_questions = question_nums[paired_count:]
                    entities['incomplete'] = {
                        'type': 'MISSING_MARKS',
                        'message': f"Missing marks for question(s): {', '.join(map(str, missing_questions))}",
                        'missing_questions': missing_questions,
                        'paired_updates': updates.copy(),
                    }
                elif len(marks_nums) > len(question_nums):
                    # More marks than questions - extra marks provided
                    extra_marks = marks_nums[paired_count:]
                    entities['incomplete'] = {
                        'type': 'EXTRA_MARKS',
                        'message': f"Extra mark(s) without questions: {', '.join(map(str, extra_marks))}",
                        'extra_marks': extra_marks,
                        'paired_updates': updates.copy(),
                    }

                logger.info(f"Partial parsing: {len(updates)} updates paired, {len(missing_questions)} missing")

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
        # EXPANDED: Section 2 Edge Cases - Subject Name Mishearings
        subject_mappings = {
            # Mathematics - all variations
            'math': 'MATH', 'maths': 'MATH', 'mathematics': 'MATH', 'mathematic': 'MATH',
            'match': 'MATH', 'mass': 'MATH', 'moths': 'MATH', 'mats': 'MATH',
            'mouth': 'MATH', 'meth': 'MATH', 'mess': 'MATH', 'mat': 'MATH',

            # Hindi - all variations
            'hindi': 'HINDI', 'indy': 'HINDI', 'indie': 'HINDI', 'hind': 'HINDI',
            'hendy': 'HINDI', 'hindy': 'HINDI', 'indi': 'HINDI', 'hindu': 'HINDI',

            # English - all variations
            'english': 'ENGLISH', 'inglish': 'ENGLISH', 'englis': 'ENGLISH',
            'enlist': 'ENGLISH', 'eng': 'ENGLISH',

            # Science - all variations
            'science': 'SCIENCE', 'signs': 'SCIENCE', 'silence': 'SCIENCE',
            'sience': 'SCIENCE', 'scince': 'SCIENCE', 'sins': 'SCIENCE', 'sin': 'SCIENCE', 'sci': 'SCIENCE',

            # Social Studies - all variations
            'social': 'SOCIAL', 'social studies': 'SOCIAL', 'soshul': 'SOCIAL',
            'so shall': 'SOCIAL', 'so shell': 'SOCIAL', 'sst': 'SOCIAL',

            # Computer - all variations
            'computer': 'COMPUTER', 'compote': 'COMPUTER', 'komputer': 'COMPUTER',
            'cs': 'COMPUTER', 'comp': 'COMPUTER',

            # Physical Education
            'physical education': 'PE', 'pe': 'PE', 'physical': 'PE',
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
            if subject_text in ['roll', 'rule', 'class', 'grade', 'number', 'section', 'update', 'marks', 'for', 'of', 'student']:
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

        # ============================================================
        # SECTION 3: Marks Validation - Detect suspicious values
        # ============================================================
        validated_marks = {}
        for subject, marks in marks_dict.items():
            validated_marks[subject] = cls._validate_marks_value(marks)

        logger.info(f"Extracted subject marks (validated): {validated_marks}")
        return validated_marks

    @classmethod
    def _validate_marks_value(cls, marks):
        """
        Validate and potentially correct marks value.

        Section 3 Edge Case: Number Confusion Handling
        - Detects values > 100 (likely error)
        - Flags suspicious teen/ty confusion (15 vs 50)
        - Returns corrected value or original if valid

        Args:
            marks: The marks value to validate

        Returns:
            int/float: Validated marks value
        """
        # If marks > 100, it's definitely an error
        if marks > 100:
            logger.warning(f"Marks value {marks} exceeds 100 - likely error")
            # Try to extract a reasonable value
            # If it's like 150, maybe they said "15" and we misheard
            if 100 < marks < 200:
                corrected = marks - 100
                logger.info(f"  Attempting correction: {marks} -> {corrected}")
                return corrected
            return min(marks, 100)  # Cap at 100

        # Valid range
        return marks

    @classmethod
    def _detect_teen_ty_confusion(cls, original_text, detected_number):
        """
        Detect potential teen/ty number confusion.

        Section 3 Edge Case: 15 vs 50, 13 vs 30, etc.

        Args:
            original_text: Original transcription
            detected_number: The number we detected

        Returns:
            dict: {
                'value': detected_number,
                'confidence': 'high'|'medium'|'low',
                'alternatives': [list of possible values]
            }
        """
        teen_ty_pairs = {
            13: 30, 30: 13,
            14: 40, 40: 14,
            15: 50, 50: 15,
            16: 60, 60: 16,
            17: 70, 70: 17,
            18: 80, 80: 18,
            19: 90, 90: 19,
        }

        result = {
            'value': detected_number,
            'confidence': 'high',
            'alternatives': []
        }

        if detected_number in teen_ty_pairs:
            alternative = teen_ty_pairs[detected_number]
            result['confidence'] = 'medium'
            result['alternatives'] = [alternative]
            logger.info(f"Teen/Ty confusion possible: {detected_number} might be {alternative}")

        return result

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

            # Check for individual roll number (also support "student")
            roll_patterns = [
                r'(?:student|roll|rule)[\.\s]+(?:number|no\.?|num|#)?[\.\s]*(\d+)',
                r'(?:student|roll|rule)[\.\s]+(\d+)',
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

        # Extract excluded roll numbers (e.g., "except roll 2, 3" or "except students 2 and 3")
        except_match = re.search(r'except\s+(?:roll|role|student|students|rule)?\s*(?:number|no\.?|num)?\s*([\d\s,and]+)', text, re.IGNORECASE)
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
        - "Show details of student 5 class 8B"
        """
        if context is None:
            context = {}

        entities = {}

        # Extract roll number (handle "rule" as speech recognition error for "roll", allow periods)
        # Also support "student" as alternative
        roll_patterns = [
            r'(?:student|roll|rule)[\.\s]+(?:number|no\.?|num|#)?[\.\s]*(\d+)',
            r'(?:student|roll|rule)[\.\s]+(\d+)',
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
        - "Open 1st A attendance"
        - "Open class 2B marks"
        - "Open first B final term" (spelled ordinals with exam type)
        """
        if context is None:
            context = {}

        entities = {}

        # Map spelled ordinals to numbers
        ordinal_map = {
            'first': 1, 'second': 2, 'third': 3, 'fourth': 4, 'fifth': 5,
            'sixth': 6, 'seventh': 7, 'eighth': 8, 'ninth': 9, 'tenth': 10
        }

        # Check for spelled ordinals first: "first B", "second A", etc.
        spelled_ordinal_match = re.search(
            r'(?:open|go\s+to)\s+(?:class\s+)?(first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth)\s+([a-z])',
            text, re.IGNORECASE
        )
        if spelled_ordinal_match:
            ordinal_word = spelled_ordinal_match.group(1).lower()
            entities['class'] = ordinal_map.get(ordinal_word, 1)
            entities['section'] = spelled_ordinal_match.group(2).upper()
            logger.info(f"Extracted class {entities['class']} and section {entities['section']} from spelled ordinal")
        else:
            # Extract class (grade number) - try multiple patterns
            class_patterns = [
                r'class\s+(\d+)',
                r'grade\s+(\d+)',
                # Ordinal patterns: "1st", "2nd", "3rd", "4th" with optional marks/attendance
                r'(\d+)(?:st|nd|rd|th)\s*[a-z]?\s*(?:marks?|attendance)?',
                # Direct number before section letter: "open 1A marks" or "open 2c"
                r'(?:open|go\s+to)\s+(?:class\s+)?(\d+)\s*[a-z]',
            ]
            for pattern in class_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    entities['class'] = int(match.group(1))
                    logger.info(f"Extracted class {entities['class']} using pattern: {pattern}")
                    break

            # Extract section - try multiple patterns
            section_patterns = [
                r'class\s+\d+\s*([A-Za-z])\b',  # "class 1A" or "class 1 A"
                r'section\s+([A-Za-z])\b',  # "section A"
                # Ordinal with section: "1st A marks", "2nd c", "3rd b"
                r'\d+(?:st|nd|rd|th)\s+([A-Za-z])\b',  # "2nd c" - with space between ordinal and letter
                r'\d+(?:st|nd|rd|th)([A-Za-z])\s*(?:marks?|attendance)',  # "1stA marks" - no space
                # Direct patterns: "open 1A marks" or "open 2c"
                r'(?:open|go\s+to)\s+(?:class\s+)?\d+\s*([A-Za-z])\b',  # "open 2c" or "go to 2c"
            ]
            for pattern in section_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    entities['section'] = match.group(1).upper()
                    logger.info(f"Extracted section {entities['section']} using pattern: {pattern}")
                    break

        # Extract exam type if present: midterm, final, unit test (handles normalized forms too)
        text_lower = text.lower()
        if 'mid' in text_lower or 'midterm' in text_lower:
            entities['exam_type'] = 'MIDTERM'
            entities['exam_type_display'] = 'Midterm Exam'
            logger.info("Extracted exam type: MIDTERM")
        elif 'final' in text_lower:
            entities['exam_type'] = 'FINAL'
            entities['exam_type_display'] = 'Final Exam'
            logger.info("Extracted exam type: FINAL")
        elif 'unit' in text_lower or 'unittest' in text_lower:
            entities['exam_type'] = 'UNIT_TEST'
            entities['exam_type_display'] = 'Unit Test'
            logger.info("Extracted exam type: UNIT_TEST")

        logger.info(f"Extracted class/section entities: {entities}")
        return entities

    @classmethod
    def _extract_exam_type_entities(cls, text, context=None):
        """
        Extract exam type from navigation command.

        Expected formats:
        - "open mid term" / "open midterm"
        - "open first mid term"
        - "open final exam" / "open final"
        - "open unit test"

        Returns:
            dict with 'exam_type' key containing one of: UNIT_TEST, MIDTERM, FINAL
        """
        if context is None:
            context = {}

        entities = {}
        text_lower = text.lower()

        # Map spoken phrases to exam type values (handles normalized forms too)
        if 'mid' in text_lower or 'midterm' in text_lower:
            entities['exam_type'] = 'MIDTERM'
            entities['exam_type_display'] = 'Midterm Exam'
        elif 'final' in text_lower:
            entities['exam_type'] = 'FINAL'
            entities['exam_type_display'] = 'Final Exam'
        elif 'unit' in text_lower or 'unittest' in text_lower:
            entities['exam_type'] = 'UNIT_TEST'
            entities['exam_type_display'] = 'Unit Test'
        else:
            # Default to midterm if no match (shouldn't happen given the intent patterns)
            entities['exam_type'] = 'MIDTERM'
            entities['exam_type_display'] = 'Midterm Exam'

        logger.info(f"Extracted exam type entities: {entities}")
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

    @classmethod
    def _extract_progress_report_entities(cls, text, context=None):
        """
        Extract entities for downloading progress report.

        Expected format:
        - "Download progress report for roll 1"
        - "Download report for student 5 class 2C"
        - "Get progress report" (when context has roll_number)
        """
        if context is None:
            context = {}

        entities = {}

        # Extract roll number
        roll_patterns = [
            r'(?:student|roll|rule)[\.\s]+(?:number|no\.?|num|#)?[\.\s]*(\d+)',
            r'(?:student|roll|rule)[\.\s]+(\d+)',
        ]
        for pattern in roll_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                entities['roll_number'] = int(match.group(1))
                break

        # Extract class (grade number)
        class_patterns = [
            r'class\s+(\d+)',
            r'grade\s+(\d+)',
            r'(\d+)(?:st|nd|rd|th)\s*[a-z]',
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
            r'\d+(?:st|nd|rd|th)?\s*([A-Za-z])\b',
        ]
        for pattern in section_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                entities['section'] = match.group(1).upper()
                break

        # Use context as fallback
        if 'roll_number' not in entities and 'roll_number' in context:
            entities['roll_number'] = int(context['roll_number'])
            logger.info(f"Using roll_number from context: {context['roll_number']}")

        if 'class' not in entities and 'class' in context:
            entities['class'] = context['class']
            logger.info(f"Using class from context: {context['class']}")

        if 'section' not in entities and 'section' in context:
            entities['section'] = context['section']
            logger.info(f"Using section from context: {context['section']}")

        logger.info(f"Extracted progress report entities: {entities}")
        return entities

    # ============================================================
    # FEE MANAGEMENT ENTITY EXTRACTION
    # ============================================================

    @classmethod
    def _extract_fee_collection_entities(cls, text, context=None):
        """
        Extract entities for fee collection.

        Expected formats:
        - "collect 5000 from roll 12 class 6A cash"
        - "collect fee 5000 student 12 class 6A UPI"
        - "collect rupees 3000 from roll number 5 class 8B"
        """
        if context is None:
            context = {}

        logger.info(f"Extracting fee collection entities from: '{text}'")
        entities = {}

        # Extract amount
        amount_patterns = [
            r'collect\s+(?:rupees?\s+)?(\d+)',
            r'collect\s+(?:fee\s+)?(?:of\s+)?(?:rupees?\s+)?(\d+)',
            r'(?:amount|fee|fees)\s+(?:of\s+|is\s+)?(?:rupees?\s+)?(\d+)',
            r'(?:rupees?|rs\.?)\s+(\d+)',
            r'(\d+)\s+(?:rupees?|rs\.?)',
            r'(\d+)\s+(?:by|through|via|in)\s+(?:cash|cheque|online|upi|card|neft)',
            r'(?:deposit|submit|process|record)\s+(?:rupees?\s+)?(\d+)',
            r'(\d{3,})',  # Fallback: any 3+ digit number is likely the amount
        ]
        for pattern in amount_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                entities['amount'] = int(match.group(1))
                break

        # Extract roll number
        roll_patterns = [
            r'(?:student|roll|rule)[\.\s]+(?:number|no\.?|num|#)?[\.\s]*(\d+)',
            r'(?:from|for)\s+(?:student|roll|rule)\s+(?:number\s+)?(\d+)',
            r'(?:roll|student|rule)\s+(\d+)\s+(?:came|wants?|has|is|ka|ke|ki|se)',
            r'(?:pay|paying)\s+(?:fee|fees)\s+(?:for\s+)?(?:roll|student|rule)\s+(\d+)',
        ]
        for pattern in roll_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                entities['roll_number'] = int(match.group(1))
                break

        # Extract student name (when no roll number found)
        if 'roll_number' not in entities:
            name_patterns = [
                # "collect fee 5000 from arun garde 6th b" — amount between verb and name
                r'(?:collect|take|receive)\s+(?:fee\s+)?(?:rupees?\s+)?\d+\s+(?:from|for)\s+([a-z]+(?:\s+[a-z]+){0,2})',
                # "collect fee from arun garde"
                r'(?:collect|take|receive)\s+(?:fee|fees|payment)\s+(?:from|for|of)\s+([a-z]+(?:\s+[a-z]+){0,2})',
                r'([a-z]+(?:\s+[a-z]+)?)\s+(?:ka|ke|ki)\s+(?:fee|fees|paisa)',
            ]
            # Words that are NOT student names
            non_names = {'class', 'roll', 'student', 'rule', 'section', 'cash', 'upi', 'card',
                         'cheque', 'online', 'the', 'fee', 'fees', 'payment', 'rupees', 'rupee',
                         'half', 'partial', 'remaining', 'pending', 'tuition', 'transport', 'bus',
                         'hostel', 'exam', 'admission', 'lab', 'library', 'annual', 'grade'}
            for pattern in name_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    name = match.group(1).strip()
                    # Strip trailing ordinal/numeric tokens like "6th" from captured name
                    name = re.sub(r'\s+\d+(?:st|nd|rd|th)?\s*[a-z]?$', '', name, flags=re.IGNORECASE).strip()
                    # Strip trailing non-name words
                    name_words = name.split()
                    while name_words and name_words[-1].lower() in non_names:
                        name_words.pop()
                    name = ' '.join(name_words)
                    if name and name.lower() not in non_names:
                        entities['student_name'] = name.title()
                        break

        # Extract class + section (try combined patterns first)
        # Ordinal with section: "6th B", "3rd A"
        ordinal_section_match = re.search(r'(\d{1,2})(?:st|nd|rd|th)\s+([A-Za-z])\b', text, re.IGNORECASE)
        # "class 6B" or "class 6 B"
        class_section_match = re.search(r'class\s+(\d+)\s*([A-Za-z])', text, re.IGNORECASE)

        if ordinal_section_match:
            entities['class'] = int(ordinal_section_match.group(1))
            entities['section'] = ordinal_section_match.group(2).upper()
        elif class_section_match:
            entities['class'] = int(class_section_match.group(1))
            entities['section'] = class_section_match.group(2).upper()
        else:
            # Extract class alone
            class_patterns = [
                r'class\s+(\d+)',
                r'grade\s+(\d+)',
                r'(\d{1,2})(?:st|nd|rd|th)\b',  # bare ordinal: "6th"
            ]
            for pattern in class_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    entities['class'] = int(match.group(1))
                    break

            # Extract section alone
            section_patterns = [
                r'section\s+([A-Za-z])',
            ]
            for pattern in section_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    entities['section'] = match.group(1).upper()
                    break

        # Extract fee type
        fee_types = {
            'tuition': 'TUITION', 'transport': 'TRANSPORT', 'bus': 'TRANSPORT',
            'hostel': 'HOSTEL', 'exam': 'EXAM', 'admission': 'ADMISSION',
            'lab': 'LAB', 'library': 'LIBRARY', 'annual': 'ANNUAL',
        }
        text_lower = text.lower()
        for keyword, fee_type in fee_types.items():
            if keyword in text_lower:
                entities['fee_type'] = fee_type
                break

        # Extract payment method
        payment_methods = {
            'cash': 'CASH',
            'upi': 'UPI',
            'card': 'CARD',
            'cheque': 'CHEQUE', 'check': 'CHEQUE',
            'online': 'ONLINE', 'net banking': 'ONLINE', 'neft': 'ONLINE',
            'rtgs': 'ONLINE', 'imps': 'ONLINE',
        }
        for keyword, method in payment_methods.items():
            if keyword in text_lower:
                entities['payment_method'] = method
                break

        if 'payment_method' not in entities:
            entities['payment_method'] = 'CASH'

        # Extract partial/half flag
        if re.search(r'\b(?:half|partial|remaining|pending)\b', text_lower):
            entities['partial_payment'] = True

        # Use context as fallback
        if 'class' not in entities and 'class' in context:
            entities['class'] = context['class']
        if 'section' not in entities and 'section' in context:
            entities['section'] = context['section']

        logger.info(f"Extracted fee collection entities: {entities}")
        return entities

    @classmethod
    def _extract_fee_details_entities(cls, text, context=None):
        """Extract entities for fee details view — needs roll number, class, section."""
        if context is None:
            context = {}

        entities = {}

        # Extract roll number
        roll_patterns = [
            r'(?:student|roll|rule)[\.\s]+(?:number|no\.?|num|#)?[\.\s]*(\d+)',
            r'(?:from|for|of)\s+(?:student|roll|rule)\s+(?:number\s+)?(\d+)',
        ]
        for pattern in roll_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                entities['roll_number'] = int(match.group(1))
                break

        # Extract class + section (try combined patterns first)
        # 1. Ordinal with section: "6th B", "1st A"
        ordinal_section_match = re.search(r'(\d{1,2})(?:st|nd|rd|th)\s+([A-Za-z])\b', text, re.IGNORECASE)
        if ordinal_section_match:
            entities['class'] = int(ordinal_section_match.group(1))
            entities['section'] = ordinal_section_match.group(2).upper()
        else:
            # 2. "class 6B" or "grade 6B"
            combined_match = re.search(r'(?:class|grade)\s+(\d+)\s*([A-Za-z])\b', text, re.IGNORECASE)
            if combined_match:
                entities['class'] = int(combined_match.group(1))
                sec = combined_match.group(2).upper()
                if sec not in ('ST', 'ND', 'RD', 'TH'):
                    entities['section'] = sec
            else:
                # 3. Bare class: "class 6", "grade 6", "6th"
                class_patterns = [
                    r'(?:class|grade)\s+(\d+)',
                    r'(\d{1,2})(?:st|nd|rd|th)\b',
                ]
                for pattern in class_patterns:
                    match = re.search(pattern, text, re.IGNORECASE)
                    if match:
                        entities['class'] = int(match.group(1))
                        break

                # 4. Section alone: "section B"
                section_match = re.search(r'section\s+([A-Za-z])', text, re.IGNORECASE)
                if section_match:
                    entities['section'] = section_match.group(1).upper()

        # Use context as fallback
        if 'roll_number' not in entities and 'roll_number' in context:
            entities['roll_number'] = context['roll_number']
        if 'class' not in entities and 'class' in context:
            entities['class'] = context['class']
        if 'section' not in entities and 'section' in context:
            entities['section'] = context['section']

        return entities

    @classmethod
    def _extract_fee_page_entities(cls, text, context=None):
        """
        Extract entities for fee page navigation.

        Expected formats:
        - "open class 6A fees"
        - "open fees" (no class specified = list page)
        """
        if context is None:
            context = {}

        logger.info(f"Extracting fee page entities from: '{text}'")
        entities = {}

        # Extract class (handle ordinals: "4th", "1st", "2nd", "3rd")
        class_patterns = [
            r'class\s+(\d+)\s*(?:st|nd|rd|th)?',
            r'(\d+)\s*(?:st|nd|rd|th)?\s*([A-Za-z])\s+(?:fee|fees)',
            r'(\d+)\s*(?:st|nd|rd|th)',  # bare ordinal: "4th", "1st"
            r'(?:open|show|go\s+to|view)\s+(?:the\s+)?(?:class\s+)?(\d+)',
        ]
        for pattern in class_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                entities['class'] = int(match.group(1))
                if match.lastindex >= 2 and match.group(2):
                    sec = match.group(2).upper()
                    if sec not in ('ST', 'ND', 'RD', 'TH'):
                        entities['section'] = sec
                break

        # Extract section if not yet found
        if 'class' in entities and 'section' not in entities:
            section_match = re.search(r'class\s+\d+\s*(?:st|nd|rd|th)?\s*([A-Za-z])\b', text, re.IGNORECASE)
            if section_match:
                sec = section_match.group(1).upper()
                if sec not in ('S', 'N', 'R', 'T'):  # Avoid matching ordinal suffix letters
                    entities['section'] = sec

        logger.info(f"Extracted fee page entities: {entities}")
        return entities

    @classmethod
    def _extract_defaulters_entities(cls, text, context=None):
        """
        Extract entities for defaulters list.

        Expected formats:
        - "show defaulters class 8"
        - "show defaulters" (no class = all classes)
        """
        if context is None:
            context = {}

        logger.info(f"Extracting defaulters entities from: '{text}'")
        entities = {}

        class_match = re.search(r'class\s+(\d+)', text, re.IGNORECASE)
        if class_match:
            entities['class'] = int(class_match.group(1))

        logger.info(f"Extracted defaulters entities: {entities}")
        return entities
