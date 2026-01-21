from django.contrib import admin
from .models import Subject, ExamType, Marks, StudentGrade


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'max_marks', 'created_at']
    list_filter = ['code']
    search_fields = ['name', 'code']


@admin.register(ExamType)
class ExamTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'weightage', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name', 'code']


@admin.register(Marks)
class MarksAdmin(admin.ModelAdmin):
    list_display = ['student', 'subject', 'exam_type', 'marks_obtained', 'max_marks', 'percentage', 'entered_by', 'created_at']
    list_filter = ['exam_type', 'subject', 'student__class_section']
    search_fields = ['student__first_name', 'student__last_name', 'student__roll_number']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(StudentGrade)
class StudentGradeAdmin(admin.ModelAdmin):
    list_display = ['student', 'exam_type', 'total_marks_obtained', 'total_max_marks', 'percentage', 'grade', 'created_at']
    list_filter = ['exam_type', 'grade', 'student__class_section']
    search_fields = ['student__first_name', 'student__last_name']
    readonly_fields = ['created_at', 'updated_at']
