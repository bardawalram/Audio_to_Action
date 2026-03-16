from django.db import models
from django.utils import timezone
import uuid


class FeeStructure(models.Model):
    """
    Defines fee amounts per class, type, and term.
    """
    class FeeType(models.TextChoices):
        TUITION = 'TUITION', 'Tuition Fee'
        EXAM = 'EXAM', 'Exam Fee'
        TRANSPORT = 'TRANSPORT', 'Transport Fee'
        LAB = 'LAB', 'Lab Fee'
        SPORTS = 'SPORTS', 'Sports Fee'
        OTHER = 'OTHER', 'Other Fee'

    class Term(models.TextChoices):
        TERM_1 = 'TERM_1', 'Term 1'
        TERM_2 = 'TERM_2', 'Term 2'
        TERM_3 = 'TERM_3', 'Term 3'
        TERM_4 = 'TERM_4', 'Term 4'
        ANNUAL = 'ANNUAL', 'Annual'

    class_obj = models.ForeignKey(
        'academics.Class',
        on_delete=models.CASCADE,
        related_name='fee_structures'
    )
    fee_type = models.CharField(
        max_length=15,
        choices=FeeType.choices,
        default=FeeType.TUITION
    )
    term = models.CharField(
        max_length=10,
        choices=Term.choices,
        default=Term.TERM_1
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    academic_year = models.CharField(max_length=20, default='2024-2025')
    due_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'fee_structures'
        verbose_name = 'Fee Structure'
        verbose_name_plural = 'Fee Structures'
        unique_together = ['class_obj', 'fee_type', 'term', 'academic_year']
        ordering = ['class_obj__grade_number', 'term', 'fee_type']

    def __str__(self):
        return f"{self.class_obj.name} - {self.get_fee_type_display()} - {self.get_term_display()} - {self.amount}"


class FeePayment(models.Model):
    """
    Records individual fee payments made by students.
    """
    class PaymentMethod(models.TextChoices):
        CASH = 'CASH', 'Cash'
        UPI = 'UPI', 'UPI'
        CARD = 'CARD', 'Card'
        CHEQUE = 'CHEQUE', 'Cheque'
        ONLINE = 'ONLINE', 'Online'

    class PaymentStatus(models.TextChoices):
        PAID = 'PAID', 'Paid'
        PARTIAL = 'PARTIAL', 'Partial'
        PENDING = 'PENDING', 'Pending'
        REFUNDED = 'REFUNDED', 'Refunded'

    student = models.ForeignKey(
        'academics.Student',
        on_delete=models.CASCADE,
        related_name='fee_payments'
    )
    fee_structure = models.ForeignKey(
        FeeStructure,
        on_delete=models.CASCADE,
        related_name='payments'
    )
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(
        max_length=10,
        choices=PaymentMethod.choices,
        default=PaymentMethod.CASH
    )
    payment_status = models.CharField(
        max_length=10,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PAID
    )
    receipt_number = models.CharField(max_length=30, unique=True, blank=True)
    payment_date = models.DateTimeField(default=timezone.now)
    collected_by = models.ForeignKey(
        'authentication.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        related_name='collected_payments'
    )
    remarks = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'fee_payments'
        verbose_name = 'Fee Payment'
        verbose_name_plural = 'Fee Payments'
        ordering = ['-payment_date']
        indexes = [
            models.Index(fields=['payment_date']),
            models.Index(fields=['student', 'payment_date']),
            models.Index(fields=['receipt_number']),
        ]

    def __str__(self):
        return f"{self.student} - {self.receipt_number} - {self.amount_paid}"

    def save(self, *args, **kwargs):
        if not self.receipt_number:
            date_str = timezone.now().strftime('%Y%m%d')
            unique_id = uuid.uuid4().hex[:6].upper()
            self.receipt_number = f"RCP-{date_str}-{unique_id}"
        super().save(*args, **kwargs)


class FeeDiscount(models.Model):
    """
    Optional discounts/concessions applied to student fees.
    """
    class DiscountType(models.TextChoices):
        SIBLING = 'SIBLING', 'Sibling Discount'
        MERIT = 'MERIT', 'Merit Scholarship'
        STAFF = 'STAFF', 'Staff Ward'
        FINANCIAL = 'FINANCIAL', 'Financial Aid'
        OTHER = 'OTHER', 'Other'

    student = models.ForeignKey(
        'academics.Student',
        on_delete=models.CASCADE,
        related_name='fee_discounts'
    )
    fee_structure = models.ForeignKey(
        FeeStructure,
        on_delete=models.CASCADE,
        related_name='discounts'
    )
    discount_type = models.CharField(
        max_length=15,
        choices=DiscountType.choices,
        default=DiscountType.OTHER
    )
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2)
    approved_by = models.ForeignKey(
        'authentication.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        related_name='approved_discounts'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'fee_discounts'
        verbose_name = 'Fee Discount'
        verbose_name_plural = 'Fee Discounts'

    def __str__(self):
        return f"{self.student} - {self.get_discount_type_display()} - {self.discount_amount}"
