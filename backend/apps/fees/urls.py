from django.urls import path
from . import views

urlpatterns = [
    path('structures/', views.fee_structures, name='fee-structures'),
    path('students/<int:class_num>/<str:section_name>/', views.student_fee_status, name='student-fee-status'),
    path('student/<int:student_id>/details/', views.student_fee_details, name='student-fee-details'),
    path('collect/', views.collect_fee, name='collect-fee'),
    path('payments/', views.payment_history, name='payment-history'),
    path('reports/today/', views.today_collection, name='today-collection'),
    path('reports/defaulters/', views.defaulters, name='defaulters'),
    path('reports/class-wise/', views.classwise_report, name='classwise-report'),
    path('reports/monthly/', views.monthly_report, name='monthly-report'),
    path('dashboard/', views.dashboard, name='fee-dashboard'),
]
