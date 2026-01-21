from django.contrib import admin
from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'model_name', 'object_id', 'timestamp']
    list_filter = ['action', 'model_name', 'timestamp']
    search_fields = ['user__username', 'model_name', 'object_id', 'description']
    readonly_fields = ['user', 'action', 'model_name', 'object_id', 'old_values', 'new_values', 'ip_address', 'user_agent', 'description', 'timestamp']

    def has_add_permission(self, request):
        # Prevent manual addition of audit logs
        return False

    def has_delete_permission(self, request, obj=None):
        # Prevent deletion of audit logs
        return False
