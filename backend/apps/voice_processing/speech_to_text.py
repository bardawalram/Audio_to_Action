"""
Whisper-based speech-to-text transcription.
"""
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class WhisperTranscriber:
    """
    Handles speech-to-text transcription using Whisper model.
    """
    _model = None

    @classmethod
    def get_model(cls):
        """
        Lazy load Whisper model (loaded only when first needed).
        """
        if cls._model is None:
            import whisper

            model_size = settings.WHISPER_MODEL_SIZE
            device = settings.WHISPER_DEVICE

            logger.info(f"Loading Whisper model: {model_size} on {device}")

            # Load model
            cls._model = whisper.load_model(model_size, device=device)

            logger.info(f"Whisper model loaded successfully")

        return cls._model

    @classmethod
    def transcribe(cls, audio_file_path):
        """
        Transcribe audio file to text.

        Args:
            audio_file_path (str): Path to audio file

        Returns:
            dict: Transcription result with text and metadata
        """
        try:
            # Use mock transcription in development if PyTorch is not available
            if getattr(settings, 'USE_MOCK_TRANSCRIPTION', False):
                logger.info(f"Using MOCK transcription for: {audio_file_path}")

                # Return mock transcription for testing
                # Using classes that teacher1 has access to: 3rdC, 3rdA, 8thB, 7thC
                mock_transcriptions = [
                    "Open marks",
                    "Open attendance",
                    "Show marks for class 8B",
                    "Open attendance for class 7C",
                    "Update marks for roll 1 maths 95 hindi 88",
                    "Enter marks for roll number 1 class 8B maths 85 hindi 78 english 92",
                    "Mark all present",
                    "Mark attendance for class 8B",
                    "Marks attendance for class 8B as present",
                    "Show details of student roll number 5 class 8B",
                ]

                import random
                transcription_text = random.choice(mock_transcriptions)

                logger.info(f"Mock transcription: {transcription_text}")

                return {
                    'text': transcription_text,
                    'language': 'en',
                    'segments': []
                }

            # Real transcription with Whisper
            model = cls.get_model()

            logger.info(f"Transcribing audio file: {audio_file_path}")

            # Transcribe
            result = model.transcribe(
                audio_file_path,
                language='en',  # Can be made configurable for Hindi support later
                fp16=False if settings.WHISPER_DEVICE == 'cpu' else True
            )

            transcription_text = result['text'].strip()

            logger.info(f"Transcription completed: {transcription_text}")

            return {
                'text': transcription_text,
                'language': result.get('language', 'en'),
                'segments': result.get('segments', [])
            }

        except Exception as e:
            logger.error(f"Transcription error: {str(e)}")
            raise Exception(f"Failed to transcribe audio: {str(e)}")

    @classmethod
    def is_model_loaded(cls):
        """Check if model is already loaded."""
        return cls._model is not None
