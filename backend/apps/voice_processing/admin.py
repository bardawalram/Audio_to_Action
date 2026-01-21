from django.contrib import admin
from .models import VoiceCommand


@admin.register(VoiceCommand)
class VoiceCommandAdmin(admin.ModelAdmin):
    list_display = ['user', 'intent', 'status', 'transcription', 'created_at']
    list_filter = ['intent', 'status', 'created_at']
    search_fields = ['user__username', 'transcription']
    readonly_fields = ['created_at', 'updated_at', 'transcription', 'entities', 'confirmation_data']
    fieldsets = (
        ('Basic Info', {
            'fields': ('user', 'audio_file', 'created_at', 'updated_at')
        }),
        ('Processing', {
            'fields': ('transcription', 'intent', 'entities', 'confirmation_data')
        }),
        ('Status', {
            'fields': ('status', 'error_message')
        }),
    )
