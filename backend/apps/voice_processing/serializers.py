"""
Serializers for voice processing API.
"""
from rest_framework import serializers
from .models import VoiceCommand


class VoiceCommandUploadSerializer(serializers.Serializer):
    """
    Serializer for uploading voice command audio file.
    """
    audio_file = serializers.FileField(required=True)
    live_transcript = serializers.CharField(required=False, allow_blank=True)
    context_class = serializers.CharField(required=False, allow_blank=True)
    context_section = serializers.CharField(required=False, allow_blank=True)
    context_roll_number = serializers.CharField(required=False, allow_blank=True)
    context_subject_id = serializers.CharField(required=False, allow_blank=True)

    def validate_audio_file(self, value):
        """
        Validate audio file format and size.
        """
        from django.conf import settings

        # Check file size
        if value.size > settings.MAX_AUDIO_FILE_SIZE:
            raise serializers.ValidationError(
                f"Audio file too large. Maximum size is {settings.MAX_AUDIO_FILE_SIZE / (1024*1024)}MB"
            )

        # Check file format
        content_type = value.content_type
        if content_type not in settings.ALLOWED_AUDIO_FORMATS:
            raise serializers.ValidationError(
                f"Invalid audio format. Allowed formats: {', '.join(settings.ALLOWED_AUDIO_FORMATS)}"
            )

        return value


class VoiceCommandSerializer(serializers.ModelSerializer):
    """
    Serializer for VoiceCommand model.
    """
    entities_display = serializers.SerializerMethodField()
    confirmation_data_display = serializers.SerializerMethodField()

    class Meta:
        model = VoiceCommand
        fields = [
            'id',
            'audio_file',
            'transcription',
            'intent',
            'entities',
            'entities_display',
            'confirmation_data',
            'confirmation_data_display',
            'status',
            'error_message',
            'created_at',
            'updated_at'
        ]
        read_only_fields = [
            'id',
            'transcription',
            'intent',
            'entities',
            'confirmation_data',
            'status',
            'error_message',
            'created_at',
            'updated_at'
        ]

    def get_entities_display(self, obj):
        return obj.get_entities_display()

    def get_confirmation_data_display(self, obj):
        return obj.get_confirmation_data_display()


class VoiceCommandConfirmSerializer(serializers.Serializer):
    """
    Serializer for confirming a voice command.
    """
    confirmed = serializers.BooleanField(required=True)


class VoiceCommandListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for listing voice commands.
    """
    class Meta:
        model = VoiceCommand
        fields = [
            'id',
            'transcription',
            'intent',
            'status',
            'created_at'
        ]
