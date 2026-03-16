"""
API views for marks management.
"""
import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db import transaction
from decimal import Decimal

from .models import Marks, QuestionWiseMarks, Subject, ExamType
from .serializers import (
    QuestionWiseMarksSerializer,
    QuestionWiseMarksDetailSerializer,
    MarksWithQuestionsSerializer
)
from apps.academics.models import Student, ClassSection, Class, Section

logger = logging.getLogger(__name__)


class QuestionWiseMarksViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing question-wise marks.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = QuestionWiseMarksSerializer

    def get_queryset(self):
        """
        Filter by marks_id if provided.
        """
        queryset = QuestionWiseMarks.objects.select_related(
            'marks__student',
            'marks__subject',
            'marks__exam_type'
        )

        marks_id = self.request.query_params.get('marks_id')
        if marks_id:
            queryset = queryset.filter(marks_id=marks_id)

        return queryset

    def get_serializer_class(self):
        """Use detailed serializer for list/retrieve."""
        if self.action in ['list', 'retrieve']:
            return QuestionWiseMarksDetailSerializer
        return QuestionWiseMarksSerializer

    def perform_create(self, serializer):
        """Set the entered_by user."""
        serializer.save(entered_by=self.request.user)

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """
        Create or update question-wise marks and recalculate total.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Check if question mark already exists
        marks_id = serializer.validated_data['marks'].id
        question_number = serializer.validated_data['question_number']

        existing = QuestionWiseMarks.objects.filter(
            marks_id=marks_id,
            question_number=question_number
        ).first()

        if existing:
            # Update existing
            for key, value in serializer.validated_data.items():
                setattr(existing, key, value)
            existing.entered_by = request.user
            existing.save()
            instance = existing
        else:
            # Create new
            instance = serializer.save(entered_by=request.user)

        # Recalculate total marks
        self._recalculate_total_marks(marks_id)

        # Return with detailed serializer
        detail_serializer = QuestionWiseMarksDetailSerializer(instance)
        return Response(detail_serializer.data, status=status.HTTP_201_CREATED)

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        """Update question mark and recalculate total."""
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save(entered_by=request.user)

        # Recalculate total marks
        self._recalculate_total_marks(instance.marks.id)

        return Response(serializer.data)

    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        """Delete question mark and recalculate total."""
        instance = self.get_object()
        marks_id = instance.marks.id
        instance.delete()

        # Recalculate total marks
        self._recalculate_total_marks(marks_id)

        return Response(status=status.HTTP_204_NO_CONTENT)

    def _recalculate_total_marks(self, marks_id):
        """
        Recalculate total marks from all question-wise marks.
        """
        marks_obj = Marks.objects.get(id=marks_id)
        question_marks = QuestionWiseMarks.objects.filter(marks=marks_obj)

        total_obtained = sum(
            q.marks_obtained for q in question_marks
        )

        marks_obj.marks_obtained = total_obtained
        marks_obj.save()

        logger.info(f"Recalculated total for Marks ID {marks_id}: {total_obtained}")


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_marks_with_questions(request, class_num, section, exam_type_code):
    """
    Get all marks with question-wise breakdown for a class.

    URL: /api/v1/marks/class/{class_num}/{section}/{exam_type}/questions/
    """
    try:
        # Get class section
        class_obj = get_object_or_404(Class, grade_number=class_num)
        section_obj = get_object_or_404(Section, name=section.upper())
        exam_type = get_object_or_404(ExamType, code=exam_type_code.upper())

        class_section = ClassSection.objects.filter(
            class_obj=class_obj,
            section=section_obj
        ).order_by('-academic_year').first()

        if not class_section:
            return Response(
                {'error': f'Class {class_num}{section} not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Get all students
        students = Student.objects.filter(
            class_section=class_section,
            is_active=True
        ).order_by('roll_number')

        # Get or create marks for each student and subject
        subjects = Subject.objects.filter(is_active=True) if hasattr(Subject, 'is_active') else Subject.objects.all()

        response_data = []
        for student in students:
            student_data = {
                'student_id': student.id,
                'roll_number': student.roll_number,
                'name': student.get_full_name(),
                'subjects': []
            }

            for subject in subjects:
                marks_obj, _ = Marks.objects.get_or_create(
                    student=student,
                    subject=subject,
                    exam_type=exam_type,
                    defaults={
                        'marks_obtained': 0,
                        'max_marks': subject.max_marks,
                        'entered_by': request.user
                    }
                )

                # Get question-wise marks
                question_marks = QuestionWiseMarks.objects.filter(
                    marks=marks_obj
                ).order_by('question_number')

                student_data['subjects'].append({
                    'subject_id': subject.id,
                    'subject_name': subject.name,
                    'subject_code': subject.code,
                    'marks_id': marks_obj.id,
                    'total_marks': float(marks_obj.marks_obtained),
                    'max_marks': marks_obj.max_marks,
                    'questions': [
                        {
                            'id': q.id,
                            'question_number': q.question_number,
                            'max_marks': float(q.max_marks),
                            'marks_obtained': float(q.marks_obtained)
                        }
                        for q in question_marks
                    ]
                })

            response_data.append(student_data)

        return Response(response_data, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error getting marks with questions: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def bulk_update_question_marks(request):
    """
    Bulk update question-wise marks.

    Request body:
    {
        "marks_id": 123,
        "questions": [
            {"question_number": 1, "max_marks": 4, "marks_obtained": 3},
            {"question_number": 2, "max_marks": 8, "marks_obtained": 6}
        ]
    }
    """
    try:
        marks_id = request.data.get('marks_id')
        questions = request.data.get('questions', [])

        if not marks_id:
            return Response(
                {'error': 'marks_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        marks_obj = get_object_or_404(Marks, id=marks_id)

        updated_questions = []
        for q_data in questions:
            question_mark, created = QuestionWiseMarks.objects.update_or_create(
                marks=marks_obj,
                question_number=q_data['question_number'],
                defaults={
                    'max_marks': Decimal(str(q_data['max_marks'])),
                    'marks_obtained': Decimal(str(q_data['marks_obtained'])),
                    'entered_by': request.user
                }
            )
            updated_questions.append(question_mark)

        # Recalculate total
        total_obtained = sum(q.marks_obtained for q in updated_questions)
        marks_obj.marks_obtained = total_obtained
        marks_obj.save()

        return Response({
            'success': True,
            'total_marks': float(total_obtained),
            'questions_updated': len(updated_questions)
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error bulk updating question marks: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ============================================================
# REPORTS & ANALYTICS API
# ============================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def reports_overview(request):
    """
    Get overview data for reports dashboard.

    Returns:
    - Total students
    - Total classes
    - Average marks
    - Average attendance
    - Class performance list
    - Top performers
    - Attendance stats
    """
    try:
        from apps.academics.models import Student, ClassSection
        from apps.attendance.models import AttendanceSession, AttendanceRecord
        from django.db.models import Avg, Count, Sum
        from datetime import date

        # Get total counts
        total_students = Student.objects.filter(is_active=True).count()
        total_classes = ClassSection.objects.count()

        # Calculate average marks
        all_marks = Marks.objects.all()
        if all_marks.exists():
            total_obtained = sum(m.marks_obtained for m in all_marks)
            total_max = sum(m.max_marks for m in all_marks)
            average_marks = (float(total_obtained) / total_max * 100) if total_max > 0 else 0
        else:
            average_marks = 0

        # Calculate attendance stats
        today = date.today()
        today_sessions = AttendanceSession.objects.filter(date=today)
        total_today_records = AttendanceRecord.objects.filter(session__date=today).count()
        present_today = AttendanceRecord.objects.filter(session__date=today, status='PRESENT').count()
        absent_today = total_today_records - present_today

        # Overall attendance percentage
        all_records = AttendanceRecord.objects.all()
        if all_records.exists():
            total_records = all_records.count()
            total_present = all_records.filter(status='PRESENT').count()
            overall_attendance = (total_present / total_records * 100) if total_records > 0 else 0
        else:
            overall_attendance = 0

        # Class performance
        class_performance = []
        for cs in ClassSection.objects.all()[:10]:
            students = Student.objects.filter(class_section=cs, is_active=True)
            if students.exists():
                student_ids = students.values_list('id', flat=True)
                class_marks = Marks.objects.filter(student_id__in=student_ids)
                if class_marks.exists():
                    total_obt = sum(m.marks_obtained for m in class_marks)
                    total_max = sum(m.max_marks for m in class_marks)
                    avg = (float(total_obt) / total_max * 100) if total_max > 0 else 0
                else:
                    avg = 0
                class_performance.append({
                    'class': f"{cs.class_obj.grade_number}{cs.section.name}",
                    'average': round(avg, 1),
                    'students': students.count()
                })

        # Top performers
        top_performers = []
        students_with_marks = Student.objects.filter(is_active=True)
        student_percentages = []

        for student in students_with_marks:
            student_marks = Marks.objects.filter(student=student)
            if student_marks.exists():
                total_obt = sum(m.marks_obtained for m in student_marks)
                total_max = sum(m.max_marks for m in student_marks)
                if total_max > 0:
                    percentage = (float(total_obt) / total_max * 100)
                    student_percentages.append({
                        'student': student,
                        'percentage': percentage
                    })

        # Sort and get top 5
        student_percentages.sort(key=lambda x: x['percentage'], reverse=True)
        for idx, sp in enumerate(student_percentages[:5]):
            student = sp['student']
            top_performers.append({
                'name': student.get_full_name(),
                'class': f"{student.class_section.class_obj.grade_number}{student.class_section.section.name}",
                'percentage': round(sp['percentage'], 1),
                'rank': idx + 1
            })

        return Response({
            'total_students': total_students,
            'total_classes': total_classes,
            'average_marks': round(average_marks, 1),
            'class_performance': class_performance,
            'top_performers': top_performers,
            'attendance_stats': {
                'overall_percentage': round(overall_attendance, 1),
                'present_today': present_today,
                'absent_today': absent_today,
                'trend': 'up',
                'trend_value': 2.3
            }
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error getting reports overview: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def class_report(request, class_num, section):
    """
    Get detailed report for a specific class.

    Returns:
    - Class info
    - Subject-wise performance
    - Grade distribution
    - Student rankings
    """
    try:
        from apps.academics.models import Student, ClassSection
        from apps.marks.utils import calculate_grade

        # Get class section
        class_obj = get_object_or_404(Class, grade_number=class_num)
        section_obj = get_object_or_404(Section, name=section.upper())

        class_section = ClassSection.objects.filter(
            class_obj=class_obj,
            section=section_obj
        ).order_by('-academic_year').first()

        if not class_section:
            return Response(
                {'error': f'Class {class_num}{section} not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Get students
        students = Student.objects.filter(
            class_section=class_section,
            is_active=True
        ).order_by('roll_number')

        # Get subjects
        subjects = Subject.objects.all()

        # Subject-wise performance
        subject_performance = []
        for subject in subjects:
            subject_marks = Marks.objects.filter(
                student__class_section=class_section,
                subject=subject
            )
            if subject_marks.exists():
                marks_list = [float(m.marks_obtained) for m in subject_marks]
                avg = sum(marks_list) / len(marks_list)
                highest = max(marks_list)
                lowest = min(marks_list)
            else:
                avg, highest, lowest = 0, 0, 0

            subject_performance.append({
                'name': subject.name,
                'average': round(avg, 1),
                'highest': int(highest),
                'lowest': int(lowest)
            })

        # Student rankings
        student_rankings = []
        grade_counts = {}

        for student in students:
            student_marks = Marks.objects.filter(student=student)
            total_obtained = sum(float(m.marks_obtained) for m in student_marks)
            total_max = sum(m.max_marks for m in student_marks) if student_marks.exists() else 500

            percentage = (total_obtained / total_max * 100) if total_max > 0 else 0
            grade = calculate_grade(percentage)

            # Count grades
            grade_counts[grade] = grade_counts.get(grade, 0) + 1

            student_rankings.append({
                'roll': student.roll_number,
                'name': student.get_full_name(),
                'total': int(total_obtained),
                'percentage': round(percentage, 1),
                'grade': grade
            })

        # Sort by percentage
        student_rankings.sort(key=lambda x: x['percentage'], reverse=True)

        # Grade distribution
        total_students = len(student_rankings)
        grade_distribution = [
            {
                'grade': grade,
                'count': count,
                'percentage': round(count / total_students * 100) if total_students > 0 else 0
            }
            for grade, count in sorted(grade_counts.items())
        ]

        return Response({
            'class_name': f"{class_num}{section}",
            'total_students': total_students,
            'subjects': subject_performance,
            'grade_distribution': grade_distribution,
            'students': student_rankings
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error getting class report: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
