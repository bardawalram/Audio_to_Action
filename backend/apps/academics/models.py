from django.db import models


class Class(models.Model):
    """
    Represents a grade/standard (e.g., 1st, 2nd, 9th, 10th).
    """
    name = models.CharField(max_length=50)  # e.g., "1st", "9th"
    grade_number = models.IntegerField(unique=True)  # 1-10
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'classes'
        verbose_name = 'Class'
        verbose_name_plural = 'Classes'
        ordering = ['grade_number']

    def __str__(self):
        return f"Class {self.name}"


class Section(models.Model):
    """
    Represents a section (e.g., A, B, C).
    """
    name = models.CharField(max_length=10, unique=True)  # A, B, C
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'sections'
        verbose_name = 'Section'
        verbose_name_plural = 'Sections'
        ordering = ['name']

    def __str__(self):
        return f"Section {self.name}"


class ClassSection(models.Model):
    """
    Combines Class and Section for a specific academic year.
    Example: 9th A for 2024-2025
    """
    class_obj = models.ForeignKey(
        Class,
        on_delete=models.CASCADE,
        related_name='class_sections'
    )
    section = models.ForeignKey(
        Section,
        on_delete=models.CASCADE,
        related_name='class_sections'
    )
    academic_year = models.CharField(max_length=20)  # e.g., "2024-2025"
    max_students = models.IntegerField(default=30)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'class_sections'
        verbose_name = 'Class Section'
        verbose_name_plural = 'Class Sections'
        unique_together = ['class_obj', 'section', 'academic_year']
        ordering = ['class_obj__grade_number', 'section__name']

    def __str__(self):
        return f"{self.class_obj.name}{self.section.name} ({self.academic_year})"


class Student(models.Model):
    """
    Student profile with academic details.
    """
    class Gender(models.TextChoices):
        MALE = 'MALE', 'Male'
        FEMALE = 'FEMALE', 'Female'
        OTHER = 'OTHER', 'Other'

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    roll_number = models.IntegerField()
    class_section = models.ForeignKey(
        ClassSection,
        on_delete=models.CASCADE,
        related_name='students'
    )
    date_of_birth = models.DateField()
    gender = models.CharField(
        max_length=10,
        choices=Gender.choices,
        default=Gender.MALE
    )
    father_name = models.CharField(max_length=200, blank=True, null=True)
    mother_name = models.CharField(max_length=200, blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'students'
        verbose_name = 'Student'
        verbose_name_plural = 'Students'
        unique_together = ['roll_number', 'class_section']
        ordering = ['class_section', 'roll_number']

    def __str__(self):
        return f"{self.first_name} {self.last_name} (Roll {self.roll_number})"

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"
