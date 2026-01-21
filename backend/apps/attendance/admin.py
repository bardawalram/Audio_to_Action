from django.contrib import admin
from .models import AttendanceSession, AttendanceRecord


class AttendanceRecordInline(admin.TabularInline):
    model = AttendanceRecord
    extra = 0
    fields = ['student', 'status', 'remarks']


@admin.register(AttendanceSession)
class AttendanceSessionAdmin(admin.ModelAdmin):
    list_display = ['class_section', 'date', 'marked_by', 'created_at']
    list_filter = ['date', 'class_section']
    search_fields = ['class_section__class_obj__name', 'class_section__section__name']
    inlines = [AttendanceRecordInline]


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ['student', 'session', 'status', 'created_at']
    list_filter = ['status', 'session__date', 'student__class_section']
    search_fields = ['student__first_name', 'student__last_name']
