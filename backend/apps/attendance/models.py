from django.db import models


class AttendanceSession(models.Model):
    """
    Represents an attendance marking session for a class on a specific date.
    """
    class_section = models.ForeignKey(
        'academics.ClassSection',
        on_delete=models.CASCADE,
        related_name='attendance_sessions'
    )
    date = models.DateField()
    marked_by = models.ForeignKey(
        'authentication.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        related_name='marked_attendance_sessions'
    )
    remarks = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'attendance_sessions'
        verbose_name = 'Attendance Session'
        verbose_name_plural = 'Attendance Sessions'
        unique_together = ['class_section', 'date']
        ordering = ['-date']

    def __str__(self):
        return f"{self.class_section} - {self.date}"


class AttendanceRecord(models.Model):
    """
    Individual attendance record for a student in a session.
    """
    class Status(models.TextChoices):
        PRESENT = 'PRESENT', 'Present'
        ABSENT = 'ABSENT', 'Absent'
        LATE = 'LATE', 'Late'
        EXCUSED = 'EXCUSED', 'Excused'

    session = models.ForeignKey(
        AttendanceSession,
        on_delete=models.CASCADE,
        related_name='records'
    )
    student = models.ForeignKey(
        'academics.Student',
        on_delete=models.CASCADE,
        related_name='attendance_records'
    )
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PRESENT
    )
    remarks = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'attendance_records'
        verbose_name = 'Attendance Record'
        verbose_name_plural = 'Attendance Records'
        unique_together = ['session', 'student']
        ordering = ['-session__date']

    def __str__(self):
        return f"{self.student.get_full_name()} - {self.session.date} - {self.status}"
