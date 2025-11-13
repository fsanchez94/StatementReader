from django.contrib import admin
from django.utils.html import format_html
from .models import ProcessingSession, UploadedFile, Transaction, Category, TransactionPattern, MerchantPattern, AccountHolder


@admin.register(ProcessingSession)
class ProcessingSessionAdmin(admin.ModelAdmin):
    list_display = ('session_id', 'status', 'total_files', 'processed_files', 'transaction_count', 'created_at')
    list_filter = ('status', 'created_at')
    readonly_fields = ('session_id', 'created_at')
    
    def transaction_count(self, obj):
        return obj.transactions.count()
    transaction_count.short_description = 'Transactions'


@admin.register(UploadedFile)
class UploadedFileAdmin(admin.ModelAdmin):
    list_display = ('filename', 'session', 'bank_type', 'account_type', 'account_holder', 'status', 'transaction_count', 'processed_at')
    list_filter = ('status', 'bank_type', 'account_type', 'account_holder', 'processed_at')
    search_fields = ('filename',)
    
    def transaction_count(self, obj):
        return obj.transactions.count()
    transaction_count.short_description = 'Transactions'


@admin.register(AccountHolder)
class AccountHolderAdmin(admin.ModelAdmin):
    list_display = ('name', 'color_display', 'is_default', 'file_count', 'transaction_count', 'created_at')
    list_filter = ('is_default', 'created_at')
    search_fields = ('name',)
    ordering = ('name',)

    def color_display(self, obj):
        return format_html(
            '<span style="background-color: {}; padding: 3px 10px; color: white; border-radius: 3px;">●</span> {}',
            obj.color,
            obj.color
        )
    color_display.short_description = 'Color'

    def file_count(self, obj):
        return obj.uploaded_files.count()
    file_count.short_description = 'Files'

    def transaction_count(self, obj):
        return obj.transactions.count()
    transaction_count.short_description = 'Transactions'


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'color_display', 'pattern_count', 'transaction_count', 'created_at')
    list_filter = ('parent', 'created_at')
    search_fields = ('name',)
    ordering = ('parent__name', 'name')

    def color_display(self, obj):
        return format_html(
            '<span style="color: {};">●</span> {}',
            obj.color,
            obj.color
        )
    color_display.short_description = 'Color'

    def pattern_count(self, obj):
        return obj.patterns.filter(is_active=True).count()
    pattern_count.short_description = 'Active Patterns'

    def transaction_count(self, obj):
        return obj.transaction_set.count()
    transaction_count.short_description = 'Transactions'


@admin.register(TransactionPattern)
class TransactionPatternAdmin(admin.ModelAdmin):
    list_display = ('pattern', 'category', 'match_type', 'confidence', 'is_active', 'created_by_learning', 'created_at')
    list_filter = ('match_type', 'is_active', 'created_by_learning', 'category', 'created_at')
    search_fields = ('pattern', 'category__name')
    list_editable = ('is_active', 'confidence')
    ordering = ('-confidence', 'pattern')


@admin.register(MerchantPattern)
class MerchantPatternAdmin(admin.ModelAdmin):
    list_display = ('pattern', 'normalized_name', 'match_type', 'confidence', 'is_active', 'transaction_count', 'created_at')
    list_filter = ('match_type', 'is_active', 'created_at')
    search_fields = ('pattern', 'normalized_name')
    list_editable = ('is_active', 'confidence')
    ordering = ('-confidence', 'pattern')

    def transaction_count(self, obj):
        """Count transactions that match this pattern"""
        return Transaction.objects.filter(merchant_name=obj.normalized_name).count()
    transaction_count.short_description = 'Transactions'


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('date', 'description_short', 'merchant_name', 'amount', 'transaction_type', 'category', 'account_name', 'account_holder', 'category_confidence')
    list_filter = ('transaction_type', 'category', 'account_holder', 'bank_type', 'account_type', 'manually_categorized', 'date')
    search_fields = ('description', 'original_description', 'merchant_name', 'account_name')
    date_hierarchy = 'date'
    list_editable = ('category',)
    ordering = ('-date', '-created_at')

    def description_short(self, obj):
        return obj.description[:50] + ('...' if len(obj.description) > 50 else '')
    description_short.short_description = 'Description'
    
    def save_model(self, request, obj, form, change):
        if 'category' in form.changed_data and obj.category:
            obj.manually_categorized = True
        super().save_model(request, obj, form, change)