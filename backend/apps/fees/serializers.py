from rest_framework import serializers
from .models import FeeStructure, FeePayment, FeeDiscount
from apps.academics.models import Student


class FeeStructureSerializer(serializers.ModelSerializer):
    class_name = serializers.CharField(source='class_obj.name', read_only=True)
    grade_number = serializers.IntegerField(source='class_obj.grade_number', read_only=True)
    fee_type_display = serializers.CharField(source='get_fee_type_display', read_only=True)
    term_display = serializers.CharField(source='get_term_display', read_only=True)

    class Meta:
        model = FeeStructure
        fields = [
            'id', 'class_obj', 'class_name', 'grade_number',
            'fee_type', 'fee_type_display', 'term', 'term_display',
            'amount', 'academic_year', 'due_date', 'is_active',
        ]


class FeePaymentSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()
    roll_number = serializers.IntegerField(source='student.roll_number', read_only=True)
    class_name = serializers.SerializerMethodField()
    fee_type = serializers.CharField(source='fee_structure.get_fee_type_display', read_only=True)
    term = serializers.CharField(source='fee_structure.get_term_display', read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
    payment_status_display = serializers.CharField(source='get_payment_status_display', read_only=True)
    collected_by_name = serializers.SerializerMethodField()

    class Meta:
        model = FeePayment
        fields = [
            'id', 'student', 'student_name', 'roll_number', 'class_name',
            'fee_structure', 'fee_type', 'term',
            'amount_paid', 'payment_method', 'payment_method_display',
            'payment_status', 'payment_status_display',
            'receipt_number', 'payment_date', 'collected_by', 'collected_by_name',
            'remarks',
        ]
        read_only_fields = ['receipt_number']

    def get_student_name(self, obj):
        return obj.student.get_full_name()

    def get_class_name(self, obj):
        cs = obj.student.class_section
        return f"{cs.class_obj.name}{cs.section.name}"

    def get_collected_by_name(self, obj):
        if obj.collected_by:
            return obj.collected_by.get_full_name() or obj.collected_by.username
        return None


class FeeCollectSerializer(serializers.Serializer):
    """Serializer for the fee collection endpoint."""
    student_id = serializers.IntegerField()
    fee_structure_id = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    payment_method = serializers.ChoiceField(choices=FeePayment.PaymentMethod.choices)
    remarks = serializers.CharField(required=False, allow_blank=True, default='')

    def validate_student_id(self, value):
        if not Student.objects.filter(id=value, is_active=True).exists():
            raise serializers.ValidationError("Student not found or inactive.")
        return value

    def validate_fee_structure_id(self, value):
        if not FeeStructure.objects.filter(id=value, is_active=True).exists():
            raise serializers.ValidationError("Fee structure not found or inactive.")
        return value

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero.")
        return value


class FeeDiscountSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()
    discount_type_display = serializers.CharField(source='get_discount_type_display', read_only=True)

    class Meta:
        model = FeeDiscount
        fields = [
            'id', 'student', 'student_name', 'fee_structure',
            'discount_type', 'discount_type_display',
            'discount_amount', 'approved_by', 'is_active',
        ]

    def get_student_name(self, obj):
        return obj.student.get_full_name()


class StudentFeeStatusSerializer(serializers.Serializer):
    """Read-only serializer for student fee status in a class."""
    student_id = serializers.IntegerField()
    roll_number = serializers.IntegerField()
    student_name = serializers.CharField()
    total_fees = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_paid = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_discount = serializers.DecimalField(max_digits=10, decimal_places=2)
    balance = serializers.DecimalField(max_digits=10, decimal_places=2)
    status = serializers.CharField()
