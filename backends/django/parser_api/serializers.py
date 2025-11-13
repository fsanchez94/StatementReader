from rest_framework import serializers
from .models import ProcessingSession, UploadedFile, AccountHolder


class AccountHolderSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccountHolder
        fields = ['id', 'name', 'color', 'is_default', 'created_at']
        read_only_fields = ['id', 'created_at']


class AccountHolderNestedSerializer(serializers.ModelSerializer):
    """Lightweight serializer for nested use"""
    class Meta:
        model = AccountHolder
        fields = ['id', 'name', 'color']


class UploadedFileSerializer(serializers.ModelSerializer):
    account_holder_info = AccountHolderNestedSerializer(source='account_holder_fk', read_only=True)

    class Meta:
        model = UploadedFile
        fields = ['filename', 'status', 'error_message', 'processed_at', 'bank_type', 'account_type', 'account_holder', 'account_holder_fk', 'account_holder_info']


class ProcessingSessionSerializer(serializers.ModelSerializer):
    files = UploadedFileSerializer(many=True, read_only=True)

    class Meta:
        model = ProcessingSession
        fields = ['session_id', 'status', 'total_files', 'processed_files', 'output_file', 'created_at', 'files']