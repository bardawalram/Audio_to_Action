from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'voice_processing'

router = DefaultRouter()
router.register('commands', views.VoiceCommandViewSet, basename='voice-command')

urlpatterns = [
    path('', include(router.urls)),
    path('upload/', views.upload_voice_command, name='upload'),
    path('commands/<int:command_id>/confirm/', views.confirm_voice_command, name='confirm'),
    path('commands/<int:command_id>/reject/', views.reject_voice_command, name='reject'),
]
