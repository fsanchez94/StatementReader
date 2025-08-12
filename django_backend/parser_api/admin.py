from django.contrib import admin
from .models import ProcessingSession, UploadedFile


@admin.register(ProcessingSession)
class ProcessingSessionAdmin(admin.ModelAdmin):
    list_display = ('session_id', 'status', 'total_files', 'processed_files', 'created_at')
    list_filter = ('status', 'created_at')
    readonly_fields = ('session_id', 'created_at')


@admin.register(UploadedFile)
class UploadedFileAdmin(admin.ModelAdmin):
    list_display = ('filename', 'session', 'status', 'processed_at')
    list_filter = ('status', 'processed_at')
    search_fields = ('filename',)