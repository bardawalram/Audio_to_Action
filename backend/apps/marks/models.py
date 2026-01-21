from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class Subject(models.Model):
    """
    Represents academic subjects.
    """
    class SubjectType(models.TextChoices):
        MATH = 'MATH', 'Mathematics'
        HINDI = 'HINDI', 'Hindi'
        ENGLISH = 'ENGLISH', 'English'
        SCIENCE = 'SCIENCE', 'Science'
        SOCIAL = 'SOCIAL', 'Social Studies'
        COMPUTER = 'COMPUTER', 'Computer Science'
        PHYSICAL_EDUCATION = 'PE', 'Physical Education'

    name = models.CharField(max_length=100)
    code = models.CharField(
        max_length=20,
        choices=SubjectType.choices,
        unique=True
    )
    description = models.TextField(blank=True, null=True)
    max_marks = models.IntegerField(default=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'subjects'
        verbose_name = 'Subject'
        verbose_name_plural = 'Subjects'
        ordering = ['name']

    def __str__(self):
        return self.name


class ExamType(models.Model):
    """
    Types of exams (Unit Test, Midterm, Final).
    """
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True)  # UNIT_TEST, MIDTERM, FINAL
    weightage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=100.00
    )  # Percentage weightage for final grade
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'exam_types'
        verbose_name = 'Exam Type'
        verbose_name_plural = 'Exam Types'
        ordering = ['name']

    def __str__(self):
        return self.name


class Marks(models.Model):
    """
    Individual marks for a student in a subject for an exam.
    """
    student = models.ForeignKey(
        'academics.Student',
        on_delete=models.CASCADE,
        related_name='marks'
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='marks'
    )
    exam_type = models.ForeignKey(
        ExamType,
        on_delete=models.CASCADE,
        related_name='marks'
    )
    marks_obtained = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    max_marks = models.IntegerField(default=100)
    remarks = models.TextField(blank=True, null=True)
    entered_by = models.ForeignKey(
        'authentication.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        related_name='entered_marks'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'marks'
        verbose_name = 'Marks'
        verbose_name_plural = 'Marks'
        unique_together = ['student', 'subject', 'exam_type']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.student.get_full_name()} - {self.subject.name} - {self.marks_obtained}/{self.max_marks}"

    @property
    def percentage(self):
        """Calculate percentage"""
        if self.max_marks > 0:
            return (float(self.marks_obtained) / self.max_marks) * 100
        return 0


class StudentGrade(models.Model):
    """
    Aggregated grade for a student for a specific exam type.
    """
    class Grade(models.TextChoices):
        A_PLUS = 'A+', 'A+ (90-100%)'
        A = 'A', 'A (80-89%)'
        B_PLUS = 'B+', 'B+ (70-79%)'
        B = 'B', 'B (60-69%)'
        C_PLUS = 'C+', 'C+ (50-59%)'
        C = 'C', 'C (40-49%)'
        D = 'D', 'D (33-39%)'
        F = 'F', 'F (0-32%)'

    student = models.ForeignKey(
        'academics.Student',
        on_delete=models.CASCADE,
        related_name='grades'
    )
    exam_type = models.ForeignKey(
        ExamType,
        on_delete=models.CASCADE,
        related_name='student_grades'
    )
    total_marks_obtained = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        default=0
    )
    total_max_marks = models.IntegerField(default=0)
    percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0
    )
    grade = models.CharField(
        max_length=3,
        choices=Grade.choices,
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'student_grades'
        verbose_name = 'Student Grade'
        verbose_name_plural = 'Student Grades'
        unique_together = ['student', 'exam_type']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.student.get_full_name()} - {self.exam_type.name} - {self.grade}"


class QuestionWiseMarks(models.Model):
    """
    Individual question-wise marks for detailed grading.
    Multiple questions roll up to the total marks in the Marks model.
    """
    marks = models.ForeignKey(
        Marks,
        on_delete=models.CASCADE,
        related_name='question_marks'
    )
    question_number = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(50)]
    )
    max_marks = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    marks_obtained = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    remarks = models.TextField(blank=True, null=True)
    entered_by = models.ForeignKey(
        'authentication.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        related_name='entered_question_marks'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'question_wise_marks'
        verbose_name = 'Question Wise Marks'
        verbose_name_plural = 'Question Wise Marks'
        unique_together = ['marks', 'question_number']
        ordering = ['marks', 'question_number']

    def __str__(self):
        return f"Q{self.question_number} - {self.marks.student.get_full_name()} - {self.marks.subject.name} - {self.marks_obtained}/{self.max_marks}"

    def clean(self):
        """Validate that obtained marks don't exceed max marks"""
        from django.core.exceptions import ValidationError
        if self.marks_obtained > self.max_marks:
            raise ValidationError('Marks obtained cannot exceed max marks')
