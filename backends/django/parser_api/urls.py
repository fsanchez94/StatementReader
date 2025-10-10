from django.urls import path
from . import views

urlpatterns = [
    path('upload/', views.upload_files, name='upload_files'),
    path('process/<uuid:session_id>/', views.process_files, name='process_files'),
    path('status/<uuid:session_id>/', views.get_session_status, name='get_session_status'),
    path('download/<uuid:session_id>/', views.download_file, name='download_file'),
    path('cleanup/<uuid:session_id>/', views.cleanup_session, name='cleanup_session'),
    path('parser-types/', views.get_parser_types, name='get_parser_types'),
    path('detect-parser/<uuid:session_id>/', views.detect_parser_types, name='detect_parser_types'),
    path('update-parsers/<uuid:session_id>/', views.update_parser_selections, name='update_parser_selections'),
    
    # New categorization endpoints
    path('categories/', views.get_categories, name='get_categories'),
    path('transactions/', views.get_transactions, name='get_transactions'),
    path('transactions/<int:transaction_id>/categorize/', views.categorize_transaction, name='categorize_transaction'),
]