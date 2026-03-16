"""
Development settings for ReATOA project.
"""
from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '[::1]']

# Use SQLite for development (easier setup)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# CORS settings for development
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3002",
    "http://127.0.0.1:3002",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
    "http://localhost:5175",
    "http://127.0.0.1:5175",
    "http://localhost:5176",
    "http://127.0.0.1:5176",
    "http://localhost:5177",
    "http://127.0.0.1:5177",
]

CORS_ALLOW_CREDENTIALS = True

# Additional development apps
INSTALLED_APPS += [
    'django_extensions',
]

# Development-specific settings
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Whisper settings
WHISPER_MODEL_SIZE = config('WHISPER_MODEL_SIZE', default='base')
WHISPER_DEVICE = config('WHISPER_DEVICE', default='cpu')

# Use mock transcription in development to bypass PyTorch issues
# Set to False to use actual Whisper transcription
USE_MOCK_TRANSCRIPTION = config('USE_MOCK_TRANSCRIPTION', default='False') == 'True'

# WhatsApp notifications — enabled in dev, prints to console without Twilio credentials
WHATSAPP_NOTIFICATIONS_ENABLED = True
