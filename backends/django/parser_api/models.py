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
    file_type = models.CharField(max_length=10, choices=[('pdf', 'PDF'), ('csv', 'CSV')], default='pdf')
    status = models.CharField(max_length=20, default='pending')
    error_message = models.TextField(blank=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    bank_type = models.CharField(max_length=50, blank=True)
    account_type = models.CharField(max_length=50, blank=True)
    account_holder = models.CharField(max_length=20, default='husband')  # Legacy field, will be removed
    account_holder_fk = models.ForeignKey('AccountHolder', on_delete=models.SET_NULL, null=True, blank=True, related_name='uploaded_files')

    class Meta:
        ordering = ['filename']


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subcategories')
    color = models.CharField(max_length=7, default='#808080')  # Hex color
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Categories'

    def __str__(self):
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name


class AccountHolder(models.Model):
    name = models.CharField(max_length=100, unique=True)
    color = models.CharField(max_length=7, default='#808080')  # Hex color for UI visualization
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # If this is being set as default, unset all others
        if self.is_default:
            AccountHolder.objects.filter(is_default=True).update(is_default=False)
        super().save(*args, **kwargs)


class Transaction(models.Model):
    # Basic transaction data
    session = models.ForeignKey(ProcessingSession, on_delete=models.CASCADE, related_name='transactions')
    uploaded_file = models.ForeignKey(UploadedFile, on_delete=models.CASCADE, related_name='transactions')
    date = models.DateField()
    description = models.TextField()
    original_description = models.TextField()
    merchant_name = models.CharField(max_length=255, blank=True, null=True)  # Normalized merchant name
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    transaction_type = models.CharField(max_length=10)  # 'credit' or 'debit'
    account_name = models.CharField(max_length=100)
    account_holder = models.CharField(max_length=20)  # Legacy field, will be removed
    account_holder_fk = models.ForeignKey(AccountHolder, on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions')

    # Bank/parser info
    bank_type = models.CharField(max_length=50)
    account_type = models.CharField(max_length=50)

    # Categorization
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    category_confidence = models.FloatField(default=0.0)  # Auto-categorization confidence
    manually_categorized = models.BooleanField(default=False)  # User manually set category

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-created_at']
        indexes = [
            models.Index(fields=['date']),
            models.Index(fields=['description']),
            models.Index(fields=['merchant_name']),
            models.Index(fields=['account_holder']),
            models.Index(fields=['bank_type', 'account_type']),
        ]
    
    def __str__(self):
        return f"{self.date} - {self.description[:50]} - {self.amount}"


class TransactionPattern(models.Model):
    pattern = models.CharField(max_length=255, unique=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='patterns')
    confidence = models.FloatField(default=1.0)  # Pattern matching confidence
    match_type = models.CharField(max_length=20, default='contains', choices=[
        ('exact', 'Exact Match'),
        ('contains', 'Contains'),
        ('starts_with', 'Starts With'),
        ('ends_with', 'Ends With'),
        ('regex', 'Regular Expression'),
    ])
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by_learning = models.BooleanField(default=False)  # Auto-created vs manually added

    class Meta:
        ordering = ['-confidence', 'pattern']
        indexes = [
            models.Index(fields=['pattern']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.pattern} -> {self.category.name} ({self.confidence:.2f})"


class MerchantPattern(models.Model):
    pattern = models.CharField(max_length=255, unique=True)
    normalized_name = models.CharField(max_length=255)  # Clean merchant name
    confidence = models.FloatField(default=1.0)  # Pattern matching confidence
    match_type = models.CharField(max_length=20, default='contains', choices=[
        ('exact', 'Exact Match'),
        ('contains', 'Contains'),
        ('starts_with', 'Starts With'),
        ('ends_with', 'Ends With'),
        ('regex', 'Regular Expression'),
    ])
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-confidence', 'pattern']
        indexes = [
            models.Index(fields=['pattern']),
            models.Index(fields=['is_active']),
        ]
        verbose_name_plural = 'Merchant Patterns'

    def __str__(self):
        return f"{self.pattern} -> {self.normalized_name} ({self.confidence:.2f})"