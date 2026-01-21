from django.contrib import admin
from .models import Class, Section, ClassSection, Student


@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    list_display = ['name', 'grade_number', 'created_at']
    list_filter = ['grade_number']
    search_fields = ['name']


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']


@admin.register(ClassSection)
class ClassSectionAdmin(admin.ModelAdmin):
    list_display = ['class_obj', 'section', 'academic_year', 'max_students', 'created_at']
    list_filter = ['academic_year', 'class_obj', 'section']
    search_fields = ['class_obj__name', 'section__name']


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['roll_number', 'first_name', 'last_name', 'class_section', 'gender', 'is_active']
    list_filter = ['class_section', 'gender', 'is_active']
    search_fields = ['first_name', 'last_name', 'roll_number', 'father_name']
    readonly_fields = ['created_at', 'updated_at']
