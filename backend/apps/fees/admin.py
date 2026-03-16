from django.contrib import admin
from .models import FeeStructure, FeePayment, FeeDiscount


@admin.register(FeeStructure)
class FeeStructureAdmin(admin.ModelAdmin):
    list_display = ['class_obj', 'fee_type', 'term', 'amount', 'academic_year', 'is_active']
    list_filter = ['fee_type', 'term', 'academic_year', 'is_active']
    search_fields = ['class_obj__name']


@admin.register(FeePayment)
class FeePaymentAdmin(admin.ModelAdmin):
    list_display = ['student', 'receipt_number', 'amount_paid', 'payment_method', 'payment_status', 'payment_date']
    list_filter = ['payment_method', 'payment_status', 'payment_date']
    search_fields = ['student__first_name', 'student__last_name', 'receipt_number']
    readonly_fields = ['receipt_number']


@admin.register(FeeDiscount)
class FeeDiscountAdmin(admin.ModelAdmin):
    list_display = ['student', 'fee_structure', 'discount_type', 'discount_amount', 'is_active']
    list_filter = ['discount_type', 'is_active']
    search_fields = ['student__first_name', 'student__last_name']
