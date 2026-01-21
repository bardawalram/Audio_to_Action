"""
Unit tests for STT normalization and batch parsing.

Tests the normalization layer that handles Whisper's homophone conversion:
- "to/too" → 2
- "for" → 4
"""
import pytest
from apps.voice_processing.intent_extractor import IntentExtractor, EntityExtractor


class TestSTTNormalization:
    """Test text normalization for STT quirks."""

    def test_for_to_4_conversion(self):
        """Test that '4' is converted back to 'for' in context."""
        text = "update marks 4 questions 1 2 3"
        normalized = IntentExtractor.normalize_stt_text(text)
        assert "for" in normalized
        assert normalized == "update marks for questions 1, 2, 3"

    def test_comma_insertion_after_questions(self):
        """Test that commas are inserted between question numbers."""
        text = "questions 1 2 3 as 4 5 6"
        normalized = IntentExtractor.normalize_stt_text(text)
        assert "1, 2, 3" in normalized
        assert "4, 5, 6" in normalized

    def test_preserves_actual_numbers(self):
        """Test that actual question/marks numbers are preserved."""
        text = "question 1 marks 4"
        normalized = IntentExtractor.normalize_stt_text(text)
        # The '4' after 'marks' should stay as 4 (it's marks value, not 'for')
        assert "marks 4" in normalized or "marks, 4" in normalized


class TestParallelListParsing:
    """Test parallel list parsing for batch updates."""

    def test_parallel_list_basic(self):
        """Test: 'questions 1, 2, 3 as 4, 5, 6'"""
        text = "update marks for questions 1, 2, 3 as 4, 5, 6"

        # Normalize first
        normalized = IntentExtractor.normalize_stt_text(text)

        # Extract intent
        intent = IntentExtractor.extract_intent(normalized)
        assert intent == 'BATCH_UPDATE_QUESTION_MARKS'

        # Extract entities
        context = {'class': 5, 'section': 'B', 'roll_number': 1, 'subject_id': 1}
        entities = EntityExtractor.extract_entities(normalized, intent, context)

        # Validate
        assert 'updates' in entities
        assert len(entities['updates']) == 3
        assert entities['updates'][0] == {'question_number': 1, 'marks_obtained': 4.0}
        assert entities['updates'][1] == {'question_number': 2, 'marks_obtained': 5.0}
        assert entities['updates'][2] == {'question_number': 3, 'marks_obtained': 6.0}

    def test_parallel_list_with_stt_quirk(self):
        """Test: 'update marks 4 questions 1 2 3 as 4 5 6' (STT converted 'for' to '4')"""
        text = "update marks 4 questions 1 2 3 as 4 5 6"

        # Normalize
        normalized = IntentExtractor.normalize_stt_text(text)
        # Should become: "update marks for questions 1, 2, 3 as 4, 5, 6"

        intent = IntentExtractor.extract_intent(normalized)
        assert intent == 'BATCH_UPDATE_QUESTION_MARKS'

        context = {'class': 5, 'section': 'B', 'roll_number': 1, 'subject_id': 1}
        entities = EntityExtractor.extract_entities(normalized, intent, context)

        assert 'updates' in entities
        assert len(entities['updates']) == 3

    def test_parallel_list_length_mismatch(self):
        """Test that mismatched lists are handled gracefully."""
        text = "questions 1, 2, 3 as 4, 5"  # 3 questions, 2 marks

        normalized = IntentExtractor.normalize_stt_text(text)
        intent = IntentExtractor.extract_intent(normalized)

        # Should still detect batch intent
        assert intent == 'BATCH_UPDATE_QUESTION_MARKS'

        context = {'class': 5, 'section': 'B', 'roll_number': 1, 'subject_id': 1}
        entities = EntityExtractor.extract_entities(normalized, intent, context)

        # Should fallback to pair-wise parsing or return empty
        # (Length mismatch should be logged as warning)
        assert 'updates' in entities


class TestPairwiseParsing:
    """Test traditional pair-wise parsing (fallback)."""

    def test_traditional_format(self):
        """Test: '1 marks 3, 2 marks 5, 3 marks 7'"""
        text = "1 marks 3, 2 marks 5, 3 marks 7"

        normalized = IntentExtractor.normalize_stt_text(text)
        intent = IntentExtractor.extract_intent(normalized)

        context = {'class': 5, 'section': 'B', 'roll_number': 1, 'subject_id': 1}
        entities = EntityExtractor.extract_entities(normalized, intent, context)

        assert 'updates' in entities
        assert len(entities['updates']) == 3

    def test_for_give_format(self):
        """Test: 'for 1 give 3, for 2 give 5'"""
        text = "for 1 give 3, for 2 give 5"

        normalized = IntentExtractor.normalize_stt_text(text)
        intent = IntentExtractor.extract_intent(normalized)

        context = {'class': 5, 'section': 'B', 'roll_number': 1, 'subject_id': 1}
        entities = EntityExtractor.extract_entities(normalized, intent, context)

        assert 'updates' in entities
        assert len(entities['updates']) == 2


class TestRealWorldExamples:
    """Test real-world transcription examples from Whisper."""

    def test_example1_spoken_for(self):
        """
        Spoken: "Update marks for questions 1, 2, 3 as 4, 5, 6"
        Whisper: "update marks 4 questions 1 2 3 as 4 5 6"
        """
        whisper_output = "update marks 4 questions 1 2 3 as 4 5 6"

        normalized = IntentExtractor.normalize_stt_text(whisper_output)
        intent = IntentExtractor.extract_intent(normalized)

        assert intent == 'BATCH_UPDATE_QUESTION_MARKS'

        context = {'class': 5, 'section': 'B', 'roll_number': 14, 'subject_id': 1}
        entities = EntityExtractor.extract_entities(normalized, intent, context)

        assert len(entities['updates']) == 3
        assert entities['updates'][0]['question_number'] == 1
        assert entities['updates'][0]['marks_obtained'] == 4.0

    def test_example2_decimal_marks(self):
        """Test with decimal marks."""
        text = "questions 1, 2, 3 as 4.5, 5.5, 6.5"

        normalized = IntentExtractor.normalize_stt_text(text)
        intent = IntentExtractor.extract_intent(normalized)

        context = {'class': 5, 'section': 'B', 'roll_number': 1, 'subject_id': 1}
        entities = EntityExtractor.extract_entities(normalized, intent, context)

        assert len(entities['updates']) == 3
        assert entities['updates'][0]['marks_obtained'] == 4.5
        assert entities['updates'][1]['marks_obtained'] == 5.5
        assert entities['updates'][2]['marks_obtained'] == 6.5


if __name__ == '__main__':
    # Run tests with pytest
    # pytest test_stt_normalization.py -v
    pass
