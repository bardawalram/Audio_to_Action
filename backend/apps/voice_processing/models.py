from django.db import models
import json


class VoiceCommand(models.Model):
    """
    Stores voice commands with their processing status.
    """
    class Intent(models.TextChoices):
        ENTER_MARKS = 'ENTER_MARKS', 'Enter Marks'
        MARK_ATTENDANCE = 'MARK_ATTENDANCE', 'Mark Attendance'
        VIEW_STUDENT = 'VIEW_STUDENT', 'View Student Details'
        NAVIGATE_MARKS = 'NAVIGATE_MARKS', 'Navigate to Marks'
        NAVIGATE_ATTENDANCE = 'NAVIGATE_ATTENDANCE', 'Navigate to Attendance'
        OPEN_MARKS_SHEET = 'OPEN_MARKS_SHEET', 'Open Marks Sheet'
        OPEN_ATTENDANCE_SHEET = 'OPEN_ATTENDANCE_SHEET', 'Open Attendance Sheet'
        UPDATE_MARKS = 'UPDATE_MARKS', 'Update Marks in Sheet'
        COLLECT_FEE = 'COLLECT_FEE', 'Collect Fee'
        OPEN_FEE_PAGE = 'OPEN_FEE_PAGE', 'Open Fee Page'
        SHOW_DEFAULTERS = 'SHOW_DEFAULTERS', 'Show Defaulters'
        TODAY_COLLECTION = 'TODAY_COLLECTION', 'Today Collection'
        NAVIGATE_FEE_REPORTS = 'NAVIGATE_FEE_REPORTS', 'Navigate to Fee Reports'
        UNKNOWN = 'UNKNOWN', 'Unknown Intent'

    class Status(models.TextChoices):
        PENDING_CONFIRMATION = 'PENDING_CONFIRMATION', 'Pending Confirmation'
        CONFIRMED = 'CONFIRMED', 'Confirmed'
        REJECTED = 'REJECTED', 'Rejected'
        EXECUTED = 'EXECUTED', 'Executed'
        FAILED = 'FAILED', 'Failed'

    user = models.ForeignKey(
        'authentication.CustomUser',
        on_delete=models.CASCADE,
        related_name='voice_commands'
    )
    audio_file = models.FileField(upload_to='voice_commands/%Y/%m/%d/')
    transcription = models.TextField(blank=True, null=True)
    intent = models.CharField(
        max_length=35,
        choices=Intent.choices,
        blank=True,
        null=True
    )
    entities = models.JSONField(default=dict, blank=True)
    confirmation_data = models.JSONField(default=dict, blank=True)
    status = models.CharField(
        max_length=25,
        choices=Status.choices,
        default=Status.PENDING_CONFIRMATION
    )
    error_message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'voice_commands'
        verbose_name = 'Voice Command'
        verbose_name_plural = 'Voice Commands'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.intent} - {self.status}"

    def get_entities_display(self):
        """Return formatted entities for display"""
        if isinstance(self.entities, str):
            return json.loads(self.entities)
        return self.entities

    def get_confirmation_data_display(self):
        """Return formatted confirmation data for display"""
        if isinstance(self.confirmation_data, str):
            return json.loads(self.confirmation_data)
        return self.confirmation_data
