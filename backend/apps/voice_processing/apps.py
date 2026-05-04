from django.apps import AppConfig
import threading


class VoiceProcessingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.voice_processing'
    verbose_name = 'Voice Processing'

    def ready(self):
        # Preload Whisper model in background thread so first request isn't slow
        from django.conf import settings
        if not getattr(settings, 'USE_MOCK_TRANSCRIPTION', False):
            thread = threading.Thread(target=self._preload_whisper, daemon=True)
            thread.start()

    @staticmethod
    def _preload_whisper():
        try:
            from .speech_to_text import WhisperTranscriber
            WhisperTranscriber.get_model()
        except Exception:
            pass  # Non-critical — will lazy-load on first request
