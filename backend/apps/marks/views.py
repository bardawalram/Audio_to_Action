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
