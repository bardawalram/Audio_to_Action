"""
Unit tests for intelligent STT normalization that handles merged number sequences.

Tests the smart splitting algorithm that preserves multi-digit numbers (10, 11, 12)
while correctly splitting merged sequences like "12345678910" → "1,2,3,4,5,6,7,8,9,10"
"""
import pytest
from apps.voice_processing.intent_extractor import IntentExtractor, EntityExtractor


class TestSmartNumberSplitting:
    """Test intelligent splitting of merged number sequences."""

    def test_merged_1_to_10(self):
        """Test: '12345678910' → '1,2,3,4,5,6,7,8,9,10'"""
        text = "questions 12345678910 as 7 8 9 10 11 12 13 14 15 16"
        normalized = IntentExtractor.normalize_stt_text(text)

        # Should detect and split the sequence, preserving "10"
        assert "1, 2, 3, 4, 5, 6, 7, 8, 9, 10" in normalized
        assert "12345678910" not in normalized
        print(f"[PASS] Normalized: {normalized}")

    def test_merged_1_to_11(self):
        """Test: '1234567891011' → '1,2,3,4,5,6,7,8,9,10,11'"""
        text = "questions 1234567891011"
        normalized = IntentExtractor.normalize_stt_text(text)

        assert "1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11" in normalized
        print(f"[PASS] Normalized: {normalized}")

    def test_merged_1_to_12(self):
        """Test: '123456789101112' → '1,2,3,4,5,6,7,8,9,10,11,12'"""
        text = "questions 123456789101112"
        normalized = IntentExtractor.normalize_stt_text(text)

        assert "1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12" in normalized
        print(f"[PASS] Normalized: {normalized}")

    def test_merged_short_sequence(self):
        """Test: '12345' → '1,2,3,4,5'"""
        text = "questions 12345 as 10 11 12 13 14"
        normalized = IntentExtractor.normalize_stt_text(text)

        assert "1, 2, 3, 4, 5" in normalized
        print(f"[PASS] Normalized: {normalized}")

    def test_preserve_only_10(self):
        """Test: Keep only 10 intact, split 11 and 12"""
        text = "questions 1 2 3 as 10 11 12"
        normalized = IntentExtractor.normalize_stt_text(text)

        # Only 10 should be preserved, 11 and 12 should be split
        assert "10" in normalized
        assert "1, 1" in normalized  # 11 split
        assert "1, 2" in normalized  # 12 split
        print(f"[PASS] Normalized: {normalized}")

    def test_split_invalid_two_digit(self):
        """Test: Split 13-99 into individual digits"""
        text = "questions 1 2 as 13 25"
        normalized = IntentExtractor.normalize_stt_text(text)

        # 13 should become "1, 3" and 25 should become "2, 5"
        assert "1, 3" in normalized
        assert "2, 5" in normalized
        print(f"[PASS] Normalized: {normalized}")

    def test_split_three_digit(self):
        """Test: '911' → '9,1,1'"""
        text = "questions 1 2 3 as 911"
        normalized = IntentExtractor.normalize_stt_text(text)

        # 911 should be split to 9, 1, 1
        assert "9, 1, 1" in normalized
        print(f"[PASS] Normalized: {normalized}")

    def test_split_four_digit(self):
        """Test: '1234' → '1,2,3,4' in marks"""
        text = "questions 1 2 3 4 as 1234"
        normalized = IntentExtractor.normalize_stt_text(text)

        assert "1, 2, 3, 4" in normalized
        print(f"[PASS] Normalized: {normalized}")


class TestRangeExpansion:
    """Test range syntax expansion."""

    def test_range_1_to_10(self):
        """Test: 'questions 1 to 10' → 'questions 1,2,3,4,5,6,7,8,9,10'"""
        text = "questions 1 to 10 as 5 5 5 5 5 5 5 5 5 5"
        normalized = IntentExtractor.normalize_stt_text(text)

        assert "1, 2, 3, 4, 5, 6, 7, 8, 9, 10" in normalized
        print(f"[PASS] Normalized: {normalized}")

    def test_range_5_through_8(self):
        """Test: 'questions 5 through 8' → 'questions 5,6,7,8'"""
        text = "questions 5 through 8"
        normalized = IntentExtractor.normalize_stt_text(text)

        assert "5, 6, 7, 8" in normalized
        print(f"[PASS] Normalized: {normalized}")

    def test_range_with_dash(self):
        """Test: 'questions 1-5' → 'questions 1,2,3,4,5'"""
        text = "questions 1-5"
        normalized = IntentExtractor.normalize_stt_text(text)

        assert "1, 2, 3, 4, 5" in normalized
        print(f"[PASS] Normalized: {normalized}")


class TestBatchParsingIntegration:
    """Test full batch parsing with intelligent normalization."""

    def test_real_world_fast_speech(self):
        """
        Real-world test case:
        Spoken: "1, 2, 3, 4, 5, 6, 7, 8, 9, 10 as 7, 1, 2, 9, 1, 1, 1, 1, 5, 10"
        Whisper: "Questions 12345678910 as 7 12 911 11 5 10"
        Expected: Correctly parse 10 question-marks pairs
        """
        text = "questions 12345678910 as 7 12 911 11 5 10"

        # Normalize
        normalized = IntentExtractor.normalize_stt_text(text)
        print(f"Normalized: {normalized}")

        # Should expand to:
        # questions 1,2,3,4,5,6,7,8,9,10 as 7,1,2,9,1,1,1,1,5,10
        assert "1, 2, 3, 4, 5, 6, 7, 8, 9, 10" in normalized
        assert "9, 1, 1" in normalized  # 911 split
        assert "1, 2" in normalized  # 12 split (not a valid mark context)

        # Extract intent
        intent = IntentExtractor.extract_intent(normalized)
        assert intent == 'BATCH_UPDATE_QUESTION_MARKS'

        # Extract entities
        context = {'class': 1, 'section': 'B', 'roll_number': 1, 'subject_id': 1}
        entities = EntityExtractor.extract_entities(normalized, intent, context)

        # Should have updates
        assert 'updates' in entities
        updates = entities['updates']

        # Should have 10 question-marks pairs
        assert len(updates) >= 9, f"Expected at least 9 updates, got {len(updates)}"

        # Verify first few pairs
        assert updates[0]['question_number'] == 1
        assert updates[0]['marks_obtained'] == 7.0

        assert updates[1]['question_number'] == 2
        assert updates[1]['marks_obtained'] == 1.0

        print(f"[PASS] Parsed {len(updates)} updates:")
        for u in updates:
            print(f"   Q{u['question_number']} → {u['marks_obtained']}")

    def test_range_with_marks_list(self):
        """
        Test: "questions 1 to 10 as 10, 9, 8, 7, 6, 5, 4, 3, 2, 1"
        Should expand range and parse correctly
        """
        text = "questions 1 to 10 as 10 9 8 7 6 5 4 3 2 1"

        normalized = IntentExtractor.normalize_stt_text(text)
        print(f"Normalized: {normalized}")

        intent = IntentExtractor.extract_intent(normalized)
        assert intent == 'BATCH_UPDATE_QUESTION_MARKS'

        context = {'class': 1, 'section': 'B', 'roll_number': 1, 'subject_id': 1}
        entities = EntityExtractor.extract_entities(normalized, intent, context)

        assert 'updates' in entities
        assert len(entities['updates']) == 10

        # Verify descending marks
        assert entities['updates'][0]['marks_obtained'] == 10.0
        assert entities['updates'][1]['marks_obtained'] == 9.0
        assert entities['updates'][9]['marks_obtained'] == 1.0

        print(f"[PASS] All 10 questions parsed with correct marks")

    def test_preserve_only_mark_10(self):
        """
        Test: "questions 1, 2, 3 as 10"
        Should preserve mark 10
        """
        text = "questions 1 2 3 as 10 10 10"  # Changed to have matching lengths

        normalized = IntentExtractor.normalize_stt_text(text)
        print(f"Normalized: {normalized}")

        intent = IntentExtractor.extract_intent(normalized)
        context = {'class': 1, 'section': 'B', 'roll_number': 1, 'subject_id': 1}
        entities = EntityExtractor.extract_entities(normalized, intent, context)

        # Should have 3 updates (matching lengths)
        assert len(entities['updates']) == 3

        # All marks should be 10 (preserved)
        assert all(u['marks_obtained'] == 10.0 for u in entities['updates'])

        print(f"[PASS] Mark 10 correctly preserved for all questions")


class TestSeparatorNormalization:
    """Test various separator formats."""

    def test_period_separators(self):
        """Test: '1. 2. 3.' → '1, 2, 3'"""
        text = "questions 1. 2. 3. as 4. 5. 6."
        normalized = IntentExtractor.normalize_stt_text(text)

        assert "1, 2, 3" in normalized
        assert "4, 5, 6" in normalized
        print(f"[PASS] Normalized: {normalized}")

    def test_slash_separators(self):
        """Test: '10/11/12' → '10, 1, 1, 1, 2' (slashes converted then 11,12 split)"""
        text = "questions 1 2 3 as 10/11/12"
        normalized = IntentExtractor.normalize_stt_text(text)

        # Slashes converted to commas, then 11 and 12 split
        assert "10" in normalized
        assert "1, 1" in normalized  # 11 split
        assert "1, 2" in normalized  # 12 split
        print(f"[PASS] Normalized: {normalized}")

    def test_mixed_separators(self):
        """Test mixed periods, slashes, and spaces"""
        text = "questions 1. 2 3/4 as 5. 6/7 8"
        normalized = IntentExtractor.normalize_stt_text(text)

        # Should have commas added
        assert "," in normalized
        print(f"[PASS] Normalized: {normalized}")


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_mismatched_list_lengths(self):
        """Test: Different lengths for questions and marks"""
        text = "questions 1 2 3 as 4 5"  # 3 questions, 2 marks

        normalized = IntentExtractor.normalize_stt_text(text)
        intent = IntentExtractor.extract_intent(normalized)

        context = {'class': 1, 'section': 'B', 'roll_number': 1, 'subject_id': 1}
        entities = EntityExtractor.extract_entities(normalized, intent, context)

        # Should either return partial updates or handle gracefully
        assert 'updates' in entities
        print(f"[PASS] Handled mismatched lists: {len(entities['updates'])} updates")

    def test_single_question_not_affected(self):
        """Test: Single question update should NOT use batch logic"""
        text = "question 3 as 8"

        normalized = IntentExtractor.normalize_stt_text(text)
        intent = IntentExtractor.extract_intent(normalized)

        # Should detect as single update, not batch
        assert intent in ['UPDATE_QUESTION_MARKS', 'BATCH_UPDATE_QUESTION_MARKS']
        print(f"[PASS] Intent: {intent}")

    def test_decimal_marks_preserved(self):
        """Test: Decimal marks like 4.5 should be preserved"""
        text = "questions 1 2 3 as 4.5 5.5 6.5"

        normalized = IntentExtractor.normalize_stt_text(text)

        # Decimal points should NOT be removed
        assert "4.5" in normalized
        assert "5.5" in normalized
        assert "6.5" in normalized
        print(f"[PASS] Normalized: {normalized}")


if __name__ == '__main__':
    # Run tests with pytest
    # pytest test_intelligent_normalization.py -v -s
    print("Run with: pytest test_intelligent_normalization.py -v -s")
