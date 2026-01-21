"""
Serializers for marks app.
"""
from rest_framework import serializers
from .models import Marks, QuestionWiseMarks, Subject, ExamType, StudentGrade


class QuestionWiseMarksSerializer(serializers.ModelSerializer):
    """
    Serializer for question-wise marks.
    """
    class Meta:
        model = QuestionWiseMarks
        fields = [
            'id',
            'marks',
            'question_number',
            'max_marks',
            'marks_obtained',
            'remarks',
            'entered_by',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'entered_by']

    def validate(self, data):
        """
        Validate that marks_obtained doesn't exceed max_marks.
        """
        if data.get('marks_obtained', 0) > data.get('max_marks', 0):
            raise serializers.ValidationError(
                "Marks obtained cannot exceed max marks"
            )
        return data


class QuestionWiseMarksDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer with student and subject info.
    """
    student_name = serializers.CharField(
        source='marks.student.get_full_name',
        read_only=True
    )
    roll_number = serializers.IntegerField(
        source='marks.student.roll_number',
        read_only=True
    )
    subject_name = serializers.CharField(
        source='marks.subject.name',
        read_only=True
    )
    subject_code = serializers.CharField(
        source='marks.subject.code',
        read_only=True
    )

    class Meta:
        model = QuestionWiseMarks
        fields = [
            'id',
            'marks',
            'question_number',
            'max_marks',
            'marks_obtained',
            'remarks',
            'student_name',
            'roll_number',
            'subject_name',
            'subject_code',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class MarksWithQuestionsSerializer(serializers.ModelSerializer):
    """
    Marks serializer with nested question-wise marks.
    """
    question_marks = QuestionWiseMarksSerializer(many=True, read_only=True)
    student_name = serializers.CharField(
        source='student.get_full_name',
        read_only=True
    )
    roll_number = serializers.IntegerField(
        source='student.roll_number',
        read_only=True
    )
    subject_name = serializers.CharField(
        source='subject.name',
        read_only=True
    )
    subject_code = serializers.CharField(
        source='subject.code',
        read_only=True
    )

    class Meta:
        model = Marks
        fields = [
            'id',
            'student',
            'student_name',
            'roll_number',
            'subject',
            'subject_name',
            'subject_code',
            'exam_type',
            'marks_obtained',
            'max_marks',
            'remarks',
            'question_marks',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
