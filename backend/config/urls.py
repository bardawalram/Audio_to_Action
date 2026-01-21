"""
URL configuration for ReATOA project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/auth/', include('apps.authentication.urls')),
    path('api/v1/students/', include('apps.academics.urls')),
    path('api/v1/marks/', include('apps.marks.urls')),
    path('api/v1/attendance/', include('apps.attendance.urls')),
    path('api/v1/voice/', include('apps.voice_processing.urls')),
    path('api/v1/audit/', include('apps.audit.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
