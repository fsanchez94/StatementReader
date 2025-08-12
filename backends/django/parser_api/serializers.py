from rest_framework import serializers
from .models import ProcessingSession, UploadedFile


class UploadedFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UploadedFile
        fields = ['filename', 'status', 'error_message', 'processed_at', 'bank_type', 'account_type', 'account_holder']


class ProcessingSessionSerializer(serializers.ModelSerializer):
    files = UploadedFileSerializer(many=True, read_only=True)
    
    class Meta:
        model = ProcessingSession
        fields = ['session_id', 'status', 'total_files', 'processed_files', 'output_file', 'created_at', 'files']