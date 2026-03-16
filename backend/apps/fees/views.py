"""
Fee management API views.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Sum, Count, Q, F, Value, CharField
from django.db.models.functions import Coalesce
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal

from .models import FeeStructure, FeePayment, FeeDiscount
from .serializers import (
    FeeStructureSerializer,
    FeePaymentSerializer,
    FeeCollectSerializer,
    StudentFeeStatusSerializer,
)
from apps.academics.models import Class, Section, ClassSection, Student
from apps.audit.models import AuditLog

import logging
logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def fee_structures(request):
    """List fee structures, optionally filtered by class."""
    class_id = request.query_params.get('class_id')
    academic_year = request.query_params.get('academic_year', '2024-2025')

    qs = FeeStructure.objects.filter(is_active=True, academic_year=academic_year)
    if class_id:
        qs = qs.filter(class_obj_id=class_id)

    serializer = FeeStructureSerializer(qs, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def student_fee_status(request, class_num, section_name):
    """Get student-wise fee status for a class/section."""
    academic_year = request.query_params.get('academic_year', '2024-2025')

    try:
        class_obj = Class.objects.get(grade_number=class_num)
        section_obj = Section.objects.get(name=section_name.upper())
        class_section = ClassSection.objects.get(
            class_obj=class_obj,
            section=section_obj,
            academic_year=academic_year,
        )
    except (Class.DoesNotExist, Section.DoesNotExist, ClassSection.DoesNotExist):
        return Response({'error': 'Class section not found'}, status=status.HTTP_404_NOT_FOUND)

    students = Student.objects.filter(class_section=class_section, is_active=True).order_by('roll_number')

    # Get total fees for this class
    total_fees_qs = FeeStructure.objects.filter(
        class_obj=class_obj, is_active=True, academic_year=academic_year
    ).aggregate(total=Coalesce(Sum('amount'), Decimal('0')))
    total_fees = total_fees_qs['total']

    result = []
    for student in students:
        paid = FeePayment.objects.filter(
            student=student,
            fee_structure__class_obj=class_obj,
            fee_structure__academic_year=academic_year,
            payment_status__in=['PAID', 'PARTIAL'],
        ).aggregate(total=Coalesce(Sum('amount_paid'), Decimal('0')))['total']

        discount = FeeDiscount.objects.filter(
            student=student,
            fee_structure__class_obj=class_obj,
            fee_structure__academic_year=academic_year,
            is_active=True,
        ).aggregate(total=Coalesce(Sum('discount_amount'), Decimal('0')))['total']

        balance = total_fees - paid - discount
        if balance <= 0:
            fee_status = 'PAID'
        elif paid > 0:
            fee_status = 'PARTIAL'
        else:
            fee_status = 'PENDING'

        result.append({
            'student_id': student.id,
            'roll_number': student.roll_number,
            'student_name': student.get_full_name(),
            'total_fees': total_fees,
            'total_paid': paid,
            'total_discount': discount,
            'balance': balance,
            'status': fee_status,
        })

    # Also include fee structures for this class
    structures = FeeStructure.objects.filter(
        class_obj=class_obj, is_active=True, academic_year=academic_year
    )
    structures_data = FeeStructureSerializer(structures, many=True).data

    return Response({
        'class_name': f"{class_obj.name}{section_obj.name}",
        'class_num': class_num,
        'section': section_name.upper(),
        'total_fees': total_fees,
        'students': result,
        'fee_structures': structures_data,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def student_fee_details(request, student_id):
    """Get detailed fee breakdown for a single student."""
    try:
        student = Student.objects.get(id=student_id, is_active=True)
    except Student.DoesNotExist:
        return Response({'error': 'Student not found'}, status=status.HTTP_404_NOT_FOUND)

    academic_year = request.query_params.get('academic_year', '2024-2025')
    class_obj = student.class_section.class_obj

    structures = FeeStructure.objects.filter(
        class_obj=class_obj, is_active=True, academic_year=academic_year
    )

    fee_details = []
    for structure in structures:
        paid = FeePayment.objects.filter(
            student=student,
            fee_structure=structure,
            payment_status__in=['PAID', 'PARTIAL'],
        ).aggregate(total=Coalesce(Sum('amount_paid'), Decimal('0')))['total']

        discount = FeeDiscount.objects.filter(
            student=student,
            fee_structure=structure,
            is_active=True,
        ).aggregate(total=Coalesce(Sum('discount_amount'), Decimal('0')))['total']

        fee_details.append({
            'structure': FeeStructureSerializer(structure).data,
            'amount_due': structure.amount,
            'amount_paid': paid,
            'discount': discount,
            'balance': structure.amount - paid - discount,
        })

    payments = FeePayment.objects.filter(
        student=student,
        fee_structure__academic_year=academic_year,
    ).order_by('-payment_date')

    return Response({
        'student': {
            'id': student.id,
            'name': student.get_full_name(),
            'roll_number': student.roll_number,
            'class': f"{student.class_section.class_obj.name}{student.class_section.section.name}",
        },
        'fee_details': fee_details,
        'payment_history': FeePaymentSerializer(payments, many=True).data,
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def collect_fee(request):
    """Collect a fee payment and generate receipt."""
    serializer = FeeCollectSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = serializer.validated_data
    student = Student.objects.get(id=data['student_id'])
    fee_structure = FeeStructure.objects.get(id=data['fee_structure_id'])

    # Determine payment status
    already_paid = FeePayment.objects.filter(
        student=student,
        fee_structure=fee_structure,
        payment_status__in=['PAID', 'PARTIAL'],
    ).aggregate(total=Coalesce(Sum('amount_paid'), Decimal('0')))['total']

    discount = FeeDiscount.objects.filter(
        student=student,
        fee_structure=fee_structure,
        is_active=True,
    ).aggregate(total=Coalesce(Sum('discount_amount'), Decimal('0')))['total']

    remaining = fee_structure.amount - already_paid - discount
    if data['amount'] >= remaining:
        payment_status = 'PAID'
    else:
        payment_status = 'PARTIAL'

    payment = FeePayment.objects.create(
        student=student,
        fee_structure=fee_structure,
        amount_paid=data['amount'],
        payment_method=data['payment_method'],
        payment_status=payment_status,
        collected_by=request.user,
        remarks=data.get('remarks', ''),
    )

    # Create audit log
    AuditLog.objects.create(
        user=request.user,
        action='CREATE',
        model_name='FeePayment',
        object_id=str(payment.id),
        new_values={
            'student_id': student.id,
            'student_name': student.get_full_name(),
            'amount': str(payment.amount_paid),
            'receipt_number': payment.receipt_number,
            'payment_method': payment.payment_method,
        },
        description=f"Fee collected: Rs.{payment.amount_paid} from {student.get_full_name()} via {payment.payment_method}",
    )

    return Response({
        'message': 'Fee collected successfully',
        'payment': FeePaymentSerializer(payment).data,
        'receipt_number': payment.receipt_number,
    }, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def payment_history(request):
    """Get payment history with optional filters."""
    qs = FeePayment.objects.all()

    date_from = request.query_params.get('date_from')
    date_to = request.query_params.get('date_to')
    class_num = request.query_params.get('class_num')
    section = request.query_params.get('section')

    if date_from:
        qs = qs.filter(payment_date__date__gte=date_from)
    if date_to:
        qs = qs.filter(payment_date__date__lte=date_to)
    if class_num:
        qs = qs.filter(student__class_section__class_obj__grade_number=class_num)
    if section:
        qs = qs.filter(student__class_section__section__name=section.upper())

    qs = qs.order_by('-payment_date')[:100]
    serializer = FeePaymentSerializer(qs, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def today_collection(request):
    """Get today's collection summary."""
    today = timezone.now().date()

    payments_today = FeePayment.objects.filter(payment_date__date=today)

    total = payments_today.aggregate(
        total=Coalesce(Sum('amount_paid'), Decimal('0'))
    )['total']

    by_method = payments_today.values('payment_method').annotate(
        total=Sum('amount_paid'),
        count=Count('id'),
    ).order_by('payment_method')

    breakdown = [
        {
            'method': item['payment_method'],
            'amount': float(item['total'] or 0),
            'count': item['count'],
        }
        for item in by_method
    ]

    recent = payments_today.select_related(
        'student__class_section__class_obj',
        'student__class_section__section',
        'fee_structure',
        'collected_by',
    ).order_by('-payment_date')[:10]
    recent_list = []
    for p in recent:
        cs = p.student.class_section
        collected_by_name = ''
        if p.collected_by:
            collected_by_name = p.collected_by.get_full_name() or p.collected_by.username
        recent_list.append({
            'receipt_no': p.receipt_number or '',
            'student_name': p.student.get_full_name(),
            'roll_number': p.student.roll_number,
            'class': f"{cs.class_obj.name}{cs.section.name}",
            'amount': float(p.amount_paid),
            'method': p.payment_method,
            'fee_type': p.fee_structure.get_fee_type_display() if p.fee_structure else '',
            'collected_by': collected_by_name,
            'date': p.payment_date.strftime('%Y-%m-%d') if p.payment_date else '',
            'time': p.payment_date.strftime('%I:%M %p') if p.payment_date else '',
        })

    return Response({
        'date': today.isoformat(),
        'total_collected': float(total),
        'transaction_count': payments_today.count(),
        'breakdown': breakdown,
        'recent_transactions': recent_list,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def defaulters(request):
    """Get students with pending fees."""
    academic_year = request.query_params.get('academic_year', '2024-2025')
    class_num = request.query_params.get('class_num')

    students = Student.objects.filter(is_active=True)
    if class_num:
        students = students.filter(class_section__class_obj__grade_number=class_num)

    defaulter_list = []
    for student in students:
        class_obj = student.class_section.class_obj

        total_fees = FeeStructure.objects.filter(
            class_obj=class_obj, is_active=True, academic_year=academic_year
        ).aggregate(total=Coalesce(Sum('amount'), Decimal('0')))['total']

        if total_fees == 0:
            continue

        paid = FeePayment.objects.filter(
            student=student,
            fee_structure__class_obj=class_obj,
            fee_structure__academic_year=academic_year,
            payment_status__in=['PAID', 'PARTIAL'],
        ).aggregate(total=Coalesce(Sum('amount_paid'), Decimal('0')))['total']

        discount = FeeDiscount.objects.filter(
            student=student,
            fee_structure__class_obj=class_obj,
            fee_structure__academic_year=academic_year,
            is_active=True,
        ).aggregate(total=Coalesce(Sum('discount_amount'), Decimal('0')))['total']

        balance = total_fees - paid - discount
        if balance > 0:
            cs = student.class_section
            defaulter_list.append({
                'student_id': student.id,
                'roll_no': student.roll_number,
                'student_name': student.get_full_name(),
                'class': f"{cs.class_obj.name}{cs.section.name}",
                'total_fees': float(total_fees),
                'paid': float(paid),
                'balance': float(balance),
            })

    # Sort by balance descending
    defaulter_list.sort(key=lambda x: x['balance'], reverse=True)

    return Response({
        'defaulter_count': len(defaulter_list),
        'defaulters': defaulter_list,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def classwise_report(request):
    """Get class-wise collection percentage."""
    academic_year = request.query_params.get('academic_year', '2024-2025')

    classes = Class.objects.all().order_by('grade_number')
    result = []

    for class_obj in classes:
        total_fees_per_student = FeeStructure.objects.filter(
            class_obj=class_obj, is_active=True, academic_year=academic_year
        ).aggregate(total=Coalesce(Sum('amount'), Decimal('0')))['total']

        student_count = Student.objects.filter(
            class_section__class_obj=class_obj,
            class_section__academic_year=academic_year,
            is_active=True,
        ).count()

        total_expected = total_fees_per_student * student_count

        total_collected = FeePayment.objects.filter(
            student__class_section__class_obj=class_obj,
            fee_structure__academic_year=academic_year,
            payment_status__in=['PAID', 'PARTIAL'],
        ).aggregate(total=Coalesce(Sum('amount_paid'), Decimal('0')))['total']

        collection_pct = (
            round(float(total_collected) / float(total_expected) * 100, 1)
            if total_expected > 0 else 0
        )

        result.append({
            'class_name': class_obj.name,
            'grade_number': class_obj.grade_number,
            'student_count': student_count,
            'expected': float(total_expected),
            'collected': float(total_collected),
            'percentage': collection_pct,
        })

    return Response({'classes': result})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def monthly_report(request):
    """Get monthly collection trends."""
    months = int(request.query_params.get('months', 6))
    today = timezone.now().date()

    result = []
    for i in range(months - 1, -1, -1):
        month_start = (today.replace(day=1) - timedelta(days=i * 30)).replace(day=1)
        if month_start.month == 12:
            month_end = month_start.replace(year=month_start.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            month_end = month_start.replace(month=month_start.month + 1, day=1) - timedelta(days=1)

        payments = FeePayment.objects.filter(
            payment_date__date__gte=month_start,
            payment_date__date__lte=month_end,
            payment_status__in=['PAID', 'PARTIAL'],
        )

        total = payments.aggregate(
            total=Coalesce(Sum('amount_paid'), Decimal('0'))
        )['total']

        is_current = (month_start.year == today.year and month_start.month == today.month)

        result.append({
            'month': month_start.strftime('%B'),
            'year': month_start.year,
            'month_key': month_start.strftime('%Y-%m'),
            'amount': float(total),
            'transaction_count': payments.count(),
            'is_current': is_current,
        })

    return Response({'months': result})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard(request):
    """Accountant dashboard summary data."""
    today = timezone.now().date()
    academic_year = request.query_params.get('academic_year', '2024-2025')

    # Today's collection
    today_payments = FeePayment.objects.filter(payment_date__date=today)
    today_total = today_payments.aggregate(
        total=Coalesce(Sum('amount_paid'), Decimal('0'))
    )['total']
    today_count = today_payments.count()

    # Total collection this year
    year_total = FeePayment.objects.filter(
        fee_structure__academic_year=academic_year,
        payment_status__in=['PAID', 'PARTIAL'],
    ).aggregate(total=Coalesce(Sum('amount_paid'), Decimal('0')))['total']

    # Total expected
    total_students = Student.objects.filter(
        class_section__academic_year=academic_year,
        is_active=True,
    ).count()

    # Pending dues count
    pending_count = 0
    students = Student.objects.filter(
        class_section__academic_year=academic_year,
        is_active=True,
    )
    for student in students:
        class_obj = student.class_section.class_obj
        total_fees = FeeStructure.objects.filter(
            class_obj=class_obj, is_active=True, academic_year=academic_year
        ).aggregate(total=Coalesce(Sum('amount'), Decimal('0')))['total']

        paid = FeePayment.objects.filter(
            student=student,
            fee_structure__class_obj=class_obj,
            fee_structure__academic_year=academic_year,
            payment_status__in=['PAID', 'PARTIAL'],
        ).aggregate(total=Coalesce(Sum('amount_paid'), Decimal('0')))['total']

        discount = FeeDiscount.objects.filter(
            student=student,
            fee_structure__class_obj=class_obj,
            fee_structure__academic_year=academic_year,
            is_active=True,
        ).aggregate(total=Coalesce(Sum('discount_amount'), Decimal('0')))['total']

        if total_fees - paid - discount > 0:
            pending_count += 1

    # Recent transactions
    recent = FeePayment.objects.order_by('-payment_date')[:5]

    # Class-wise progress (top-level summary)
    classes = Class.objects.all().order_by('grade_number')
    class_progress = []
    for class_obj in classes:
        fees_per_student = FeeStructure.objects.filter(
            class_obj=class_obj, is_active=True, academic_year=academic_year
        ).aggregate(total=Coalesce(Sum('amount'), Decimal('0')))['total']

        sc = Student.objects.filter(
            class_section__class_obj=class_obj,
            class_section__academic_year=academic_year,
            is_active=True,
        ).count()

        expected = fees_per_student * sc
        collected = FeePayment.objects.filter(
            student__class_section__class_obj=class_obj,
            fee_structure__academic_year=academic_year,
            payment_status__in=['PAID', 'PARTIAL'],
        ).aggregate(total=Coalesce(Sum('amount_paid'), Decimal('0')))['total']

        pct = round(float(collected) / float(expected) * 100, 1) if expected > 0 else 0
        class_progress.append({
            'class_name': class_obj.name,
            'grade_number': class_obj.grade_number,
            'percentage': pct,
            'collected': collected,
            'total': expected,
        })

    return Response({
        'today_collection': {
            'total_amount': today_total,
            'transaction_count': today_count,
        },
        'year_collection': year_total,
        'total_students': total_students,
        'pending_dues_count': pending_count,
        'recent_transactions': FeePaymentSerializer(recent, many=True).data,
        'class_progress': class_progress,
    })
