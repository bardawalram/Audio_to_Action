"""
Utility functions for marks and grade calculations.
"""
from decimal import Decimal
from .models import StudentGrade, Marks


def calculate_grade(percentage):
    """
    Calculate letter grade based on percentage.

    Args:
        percentage (float): Percentage score (0-100)

    Returns:
        str: Letter grade (A+, A, B+, B, C+, C, D, F)
    """
    percentage = float(percentage)

    if percentage >= 90:
        return StudentGrade.Grade.A_PLUS
    elif percentage >= 80:
        return StudentGrade.Grade.A
    elif percentage >= 70:
        return StudentGrade.Grade.B_PLUS
    elif percentage >= 60:
        return StudentGrade.Grade.B
    elif percentage >= 50:
        return StudentGrade.Grade.C_PLUS
    elif percentage >= 40:
        return StudentGrade.Grade.C
    elif percentage >= 33:
        return StudentGrade.Grade.D
    else:
        return StudentGrade.Grade.F


def calculate_student_grade(student, exam_type):
    """
    Calculate and update the overall grade for a student for a specific exam type.

    Args:
        student: Student instance
        exam_type: ExamType instance

    Returns:
        StudentGrade: Updated or created StudentGrade instance
    """
    # Get all marks for this student and exam type
    marks = Marks.objects.filter(student=student, exam_type=exam_type)

    if not marks.exists():
        return None

    # Calculate totals
    total_marks_obtained = sum(mark.marks_obtained for mark in marks)
    total_max_marks = sum(mark.max_marks for mark in marks)

    # Calculate percentage
    if total_max_marks > 0:
        percentage = (float(total_marks_obtained) / total_max_marks) * 100
    else:
        percentage = 0

    # Get or create StudentGrade
    student_grade, created = StudentGrade.objects.get_or_create(
        student=student,
        exam_type=exam_type,
        defaults={
            'total_marks_obtained': total_marks_obtained,
            'total_max_marks': total_max_marks,
            'percentage': Decimal(str(percentage)),
            'grade': calculate_grade(percentage)
        }
    )

    # Update if already exists
    if not created:
        student_grade.total_marks_obtained = total_marks_obtained
        student_grade.total_max_marks = total_max_marks
        student_grade.percentage = Decimal(str(percentage))
        student_grade.grade = calculate_grade(percentage)
        student_grade.save()

    return student_grade


def get_student_marks_summary(student, exam_type=None):
    """
    Get a summary of marks for a student.

    Args:
        student: Student instance
        exam_type: Optional ExamType instance to filter by

    Returns:
        dict: Summary with marks and grades
    """
    marks_query = Marks.objects.filter(student=student)

    if exam_type:
        marks_query = marks_query.filter(exam_type=exam_type)

    marks_list = marks_query.select_related('subject', 'exam_type').order_by('exam_type', 'subject')

    # Group by exam type
    summary = {}
    for mark in marks_list:
        exam_name = mark.exam_type.name
        if exam_name not in summary:
            summary[exam_name] = {
                'marks': [],
                'total_obtained': 0,
                'total_max': 0,
                'percentage': 0,
                'grade': None
            }

        summary[exam_name]['marks'].append({
            'subject': mark.subject.name,
            'marks_obtained': float(mark.marks_obtained),
            'max_marks': mark.max_marks,
            'percentage': mark.percentage
        })

        summary[exam_name]['total_obtained'] += float(mark.marks_obtained)
        summary[exam_name]['total_max'] += mark.max_marks

    # Calculate percentage and grade for each exam type
    for exam_name in summary:
        if summary[exam_name]['total_max'] > 0:
            percentage = (summary[exam_name]['total_obtained'] / summary[exam_name]['total_max']) * 100
            summary[exam_name]['percentage'] = round(percentage, 2)
            summary[exam_name]['grade'] = calculate_grade(percentage)

    return summary
