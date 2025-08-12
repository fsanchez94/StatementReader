from django.db import models
import uuid


class ProcessingSession(models.Model):
    session_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default='pending')
    total_files = models.IntegerField(default=0)
    processed_files = models.IntegerField(default=0)
    output_file = models.CharField(max_length=255, blank=True)
    
    class Meta:
        ordering = ['-created_at']


class UploadedFile(models.Model):
    session = models.ForeignKey(ProcessingSession, on_delete=models.CASCADE, related_name='files')
    filename = models.CharField(max_length=255)
    file_path = models.CharField(max_length=500)
    status = models.CharField(max_length=20, default='pending')
    error_message = models.TextField(blank=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    bank_type = models.CharField(max_length=50, blank=True)
    account_type = models.CharField(max_length=50, blank=True)
    account_holder = models.CharField(max_length=20, default='husband')
    
    class Meta:
        ordering = ['filename']