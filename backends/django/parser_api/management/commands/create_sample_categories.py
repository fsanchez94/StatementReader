from django.core.management.base import BaseCommand
from parser_api.models import Category, TransactionPattern


class Command(BaseCommand):
    help = 'Create sample categories and transaction patterns'

    def handle(self, *args, **options):
        self.stdout.write("Creating sample categories and patterns...")
        
        # Create main categories
        food_category = Category.objects.get_or_create(
            name="Food & Dining",
            defaults={'color': '#FF6B6B'}
        )[0]
        
        transportation_category = Category.objects.get_or_create(
            name="Transportation",
            defaults={'color': '#4ECDC4'}
        )[0]
        
        entertainment_category = Category.objects.get_or_create(
            name="Entertainment",
            defaults={'color': '#45B7D1'}
        )[0]
        
        utilities_category = Category.objects.get_or_create(
            name="Utilities",
            defaults={'color': '#FFA07A'}
        )[0]
        
        shopping_category = Category.objects.get_or_create(
            name="Shopping",
            defaults={'color': '#98D8C8'}
        )[0]
        
        health_category = Category.objects.get_or_create(
            name="Health & Medical",
            defaults={'color': '#F7DC6F'}
        )[0]
        
        # Create subcategories
        grocery_category = Category.objects.get_or_create(
            name="Groceries",
            parent=food_category,
            defaults={'color': '#FF4757'}
        )[0]
        
        restaurant_category = Category.objects.get_or_create(
            name="Restaurants",
            parent=food_category,
            defaults={'color': '#FF3838'}
        )[0]
        
        # Create transaction patterns (common Guatemalan patterns)
        patterns = [
            # Food patterns
            ("super", food_category, "contains"),
            ("supermercado", food_category, "contains"), 
            ("paiz", grocery_category, "contains"),
            ("despensa", grocery_category, "contains"),
            ("maxi", grocery_category, "contains"),
            ("walmart", grocery_category, "contains"),
            ("restaurant", restaurant_category, "contains"),
            ("restaurante", restaurant_category, "contains"),
            ("mcdonalds", restaurant_category, "contains"),
            ("burger", restaurant_category, "contains"),
            ("pizza", restaurant_category, "contains"),
            ("kfc", restaurant_category, "contains"),
            
            # Transportation patterns
            ("gasolina", transportation_category, "contains"),
            ("combustible", transportation_category, "contains"),
            ("puma", transportation_category, "contains"),
            ("shell", transportation_category, "contains"),
            ("esso", transportation_category, "contains"),
            ("uber", transportation_category, "contains"),
            ("taxi", transportation_category, "contains"),
            
            # Utilities patterns
            ("eegsa", utilities_category, "contains"),
            ("empagua", utilities_category, "contains"),
            ("claro", utilities_category, "contains"),
            ("tigo", utilities_category, "contains"),
            ("movistar", utilities_category, "contains"),
            
            # Shopping patterns
            ("tienda", shopping_category, "contains"),
            ("almacen", shopping_category, "contains"),
            ("plaza", shopping_category, "contains"),
            ("centro", shopping_category, "contains"),
            ("mall", shopping_category, "contains"),
            
            # Health patterns
            ("farmacia", health_category, "contains"),
            ("clinica", health_category, "contains"),
            ("hospital", health_category, "contains"),
            ("medico", health_category, "contains"),
        ]
        
        created_patterns = 0
        for pattern_text, category, match_type in patterns:
            pattern, created = TransactionPattern.objects.get_or_create(
                pattern=pattern_text,
                defaults={
                    'category': category,
                    'match_type': match_type,
                    'confidence': 0.8,
                    'is_active': True
                }
            )
            if created:
                created_patterns += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {Category.objects.count()} categories '
                f'and {created_patterns} new transaction patterns'
            )
        )