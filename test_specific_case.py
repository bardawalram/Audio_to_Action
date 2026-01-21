#!/usr/bin/env python
"""
Test the specific case: questions 1,2,3,4,5,6,7,8,9,10 as 7,8,9,1,2,3,4,5,6,8
Whisper transcribes as: "12345678910 as 7891234568"
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
import django
django.setup()

from apps.voice_processing.intent_extractor import IntentExtractor, EntityExtractor
import re

print("=" * 80)
print("TESTING: questions 12345678910 as 7891234568")
print("=" * 80)

# Simulate Whisper transcription
whisper_output = "questions 12345678910 as 7891234568"
print(f"\n1. Whisper transcription: '{whisper_output}'")

# Normalize
normalized = IntentExtractor.normalize_stt_text(whisper_output)
print(f"\n2. After normalization: '{normalized}'")

# Extract intent
intent = IntentExtractor.extract_intent(normalized)
print(f"\n3. Intent detected: {intent}")

# Extract entities
context = {'class': 1, 'section': 'B', 'roll_number': 14, 'subject_id': 1}
entities = EntityExtractor.extract_entities(normalized, intent, context)

print(f"\n4. Entities extracted:")
print(f"   Total updates: {len(entities.get('updates', []))}")

if 'updates' in entities and entities['updates']:
    print(f"\n5. Question-Marks pairs:")
    for i, update in enumerate(entities['updates'], 1):
        print(f"   {i}. Q{update['question_number']:2d} -> {update['marks_obtained']:.1f} marks")

print("\n" + "=" * 80)
print("EXPECTED RESULT:")
print("  10 updates total")
print("  Q1->7, Q2->8, Q3->9, Q4->1, Q5->2, Q6->3, Q7->4, Q8->5, Q9->6, Q10->8")
print("=" * 80)

# Verify
if len(entities.get('updates', [])) == 10:
    print("\n[PASS] SUCCESS: Got 10 updates as expected!")
else:
    print(f"\n[FAIL] FAILED: Got {len(entities.get('updates', []))} updates instead of 10")

    # Debug: Show what was extracted
    print("\n[DEBUG] DEBUGGING:")
    parallel_pattern = r'questions?\s+([\d,\s]+)\s+(?:as|marks?|give)\s+([\d,\s]+)'
    match = re.search(parallel_pattern, normalized, re.IGNORECASE)

    if match:
        q_str = match.group(1)
        m_str = match.group(2)

        print(f"   Question string: '{q_str}'")
        print(f"   Marks string: '{m_str}'")

        q_nums = re.findall(r'\d+', q_str)
        m_nums = re.findall(r'\d+(?:\.\d+)?', m_str)

        print(f"   Questions found: {len(q_nums)} → {q_nums}")
        print(f"   Marks found: {len(m_nums)} → {m_nums}")
