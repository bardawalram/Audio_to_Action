from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'marks'

router = DefaultRouter()
router.register(r'question-marks', views.QuestionWiseMarksViewSet, basename='question-marks')

urlpatterns = [
    # Question-wise marks endpoints
    path('', include(router.urls)),
    path(
        'class/<int:class_num>/<str:section>/<str:exam_type_code>/questions/',
        views.get_marks_with_questions,
        name='class-marks-with-questions'
    ),
    path(
        'question-marks/bulk-update/',
        views.bulk_update_question_marks,
        name='bulk-update-question-marks'
    ),
    # Reports & Analytics endpoints
    path(
        'reports/overview/',
        views.reports_overview,
        name='reports-overview'
    ),
    path(
        'reports/class/<int:class_num>/<str:section>/',
        views.class_report,
        name='class-report'
    ),
]
