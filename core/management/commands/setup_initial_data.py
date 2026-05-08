from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import User, Region, Category, SubCategory, UserCategoryPermission
import random
from datetime import timedelta


class Command(BaseCommand):
    help = 'Set up initial data for the Agro Price Tracker application'

    def handle(self, *args, **options):
        self.stdout.write('Setting up initial data...')
        
        # Create Regions
        regions_data = [
            ('Mumbai', 'Maharashtra', 'India'),
            ('Delhi', 'Delhi', 'India'),
            ('Bangalore', 'Karnataka', 'India'),
            ('Chennai', 'Tamil Nadu', 'India'),
            ('Kolkata', 'West Bengal', 'India'),
            ('Hyderabad', 'Telangana', 'India'),
            ('Pune', 'Maharashtra', 'India'),
            ('Ahmedabad', 'Gujarat', 'India'),
            ('Jaipur', 'Rajasthan', 'India'),
            ('Lucknow', 'Uttar Pradesh', 'India'),
        ]
        
        regions = []
        for name, state, country in regions_data:
            region, created = Region.objects.get_or_create(
                name=name,
                state=state,
                defaults={'country': country}
            )
            regions.append(region)
            if created:
                self.stdout.write(f'  Created region: {name}, {state}')
        
        # Create Categories with Subcategories
        categories_data = [
            {
                'name': 'Apple',
                'icon': '🍎',
                'color': '#ef4444',
                'subcategories': [
                    ('Red Delicious', 'kg'),
                    ('Granny Smith', 'kg'),
                    ('Fuji Apple', 'kg'),
                    ('Gala Apple', 'kg'),
                    ('Kashmiri Apple', 'kg'),
                    ('Shimla Apple', 'kg'),
                ]
            },
            {
                'name': 'Mango',
                'icon': '🥭',
                'color': '#f59e0b',
                'subcategories': [
                    ('Alphonso', 'kg'),
                    ('Kesar', 'kg'),
                    ('Dasheri', 'kg'),
                    ('Langra', 'kg'),
                    ('Totapuri', 'kg'),
                    ('Badami', 'kg'),
                ]
            },
            {
                'name': 'Banana',
                'icon': '🍌',
                'color': '#eab308',
                'subcategories': [
                    ('Robusta', 'dozen'),
                    ('Red Banana', 'dozen'),
                    ('Elaichi', 'dozen'),
                    ('Nendran', 'kg'),
                    ('Grand Naine', 'dozen'),
                ]
            },
            {
                'name': 'Orange',
                'icon': '🍊',
                'color': '#f97316',
                'subcategories': [
                    ('Nagpur Orange', 'kg'),
                    ('Blood Orange', 'kg'),
                    ('Navel Orange', 'kg'),
                    ('Kinnow', 'kg'),
                    ('Malta', 'kg'),
                ]
            },
            {
                'name': 'Tomato',
                'icon': '🍅',
                'color': '#dc2626',
                'subcategories': [
                    ('Desi Tomato', 'kg'),
                    ('Hybrid Tomato', 'kg'),
                    ('Cherry Tomato', 'kg'),
                    ('Roma Tomato', 'kg'),
                ]
            },
            {
                'name': 'Potato',
                'icon': '🥔',
                'color': '#a16207',
                'subcategories': [
                    ('Jyoti', 'kg'),
                    ('Kufri Chandramukhi', 'kg'),
                    ('Kufri Bahar', 'kg'),
                    ('Kufri Pukhraj', 'kg'),
                ]
            },
            {
                'name': 'Onion',
                'icon': '🧅',
                'color': '#b45309',
                'subcategories': [
                    ('Red Onion', 'kg'),
                    ('White Onion', 'kg'),
                    ('Pink Onion', 'kg'),
                    ('Shallots', 'kg'),
                ]
            },
            {
                'name': 'Carrot',
                'icon': '🥕',
                'color': '#ea580c',
                'subcategories': [
                    ('Orange Carrot', 'kg'),
                    ('Red Carrot', 'kg'),
                    ('Ooty Carrot', 'kg'),
                    ('Baby Carrot', 'kg'),
                ]
            },
            {
                'name': 'Grapes',
                'icon': '🍇',
                'color': '#7c3aed',
                'subcategories': [
                    ('Thompson Seedless', 'kg'),
                    ('Black Grapes', 'kg'),
                    ('Red Globe', 'kg'),
                    ('Flame Seedless', 'kg'),
                ]
            },
            {
                'name': 'Watermelon',
                'icon': '🍉',
                'color': '#16a34a',
                'subcategories': [
                    ('Sugar Baby', 'kg'),
                    ('Crimson Sweet', 'kg'),
                    ('Black Diamond', 'kg'),
                    ('Yellow Watermelon', 'kg'),
                ]
            },
        ]
        
        for cat_data in categories_data:
            category, created = Category.objects.get_or_create(
                name=cat_data['name'],
                defaults={
                    'icon': cat_data['icon'],
                    'color': cat_data['color'],
                }
            )
            if created:
                self.stdout.write(f'  Created category: {category.name}')
            
            for subcat_name, unit in cat_data['subcategories']:
                subcategory, created = SubCategory.objects.get_or_create(
                    category=category,
                    name=subcat_name,
                    defaults={'unit': unit}
                )
                if created:
                    self.stdout.write(f'    Created subcategory: {subcat_name}')
        
        # Create Admin User if not exists
        admin_email = 'admin@agroprice.com'
        if not User.objects.filter(email=admin_email).exists():
            admin_user = User.objects.create_superuser(
                email=admin_email,
                password='admin123',
                first_name='Admin',
                last_name='User'
            )
            self.stdout.write(self.style.SUCCESS(f'Created admin user: {admin_email} (password: admin123)'))
        
        # Create Business Head
        bh_email = 'businesshead@agroprice.com'
        if not User.objects.filter(email=bh_email).exists():
            bh_user = User.objects.create_user(
                email=bh_email,
                password='bh123456',
                first_name='Business',
                last_name='Head',
                role='business_head',
                region=regions[0] if regions else None
            )
            self.stdout.write(self.style.SUCCESS(f'Created business head: {bh_email} (password: bh123456)'))
        
        # Create Sample Farmers
        farmer_names = [
            ('Rajesh', 'Kumar', 'farmer1@agroprice.com'),
            ('Suresh', 'Patel', 'farmer2@agroprice.com'),
            ('Mahesh', 'Singh', 'farmer3@agroprice.com'),
        ]
        
        for first_name, last_name, email in farmer_names:
            if not User.objects.filter(email=email).exists():
                farmer = User.objects.create_user(
                    email=email,
                    password='farmer123',
                    first_name=first_name,
                    last_name=last_name,
                    role='farmer',
                    region=random.choice(regions) if regions else None,
                    has_direct_access=random.choice([True, False])
                )
                
                # Add permissions to some categories
                categories = list(Category.objects.all()[:3])
                for cat in categories:
                    UserCategoryPermission.objects.create(
                        user=farmer,
                        category=cat,
                        can_view=True,
                        can_edit_price=True
                    )
                    farmer.allowed_categories.add(cat)
                
                self.stdout.write(f'  Created farmer: {email} (password: farmer123)')
        
        # Create Sample Buyers
        buyer_names = [
            ('Amit', 'Sharma', 'buyer1@agroprice.com'),
            ('Vivek', 'Gupta', 'buyer2@agroprice.com'),
            ('Priya', 'Verma', 'buyer3@agroprice.com'),
        ]
        
        for first_name, last_name, email in buyer_names:
            if not User.objects.filter(email=email).exists():
                buyer = User.objects.create_user(
                    email=email,
                    password='buyer123',
                    first_name=first_name,
                    last_name=last_name,
                    role='buyer',
                    region=random.choice(regions) if regions else None,
                    company_name=f'{first_name} Traders'
                )
                
                # Add permissions to some categories
                categories = list(Category.objects.all()[3:6])
                for cat in categories:
                    UserCategoryPermission.objects.create(
                        user=buyer,
                        category=cat,
                        can_view=True,
                        can_edit_price=True
                    )
                    buyer.allowed_categories.add(cat)
                
                self.stdout.write(f'  Created buyer: {email} (password: buyer123)')
        
        self.stdout.write(self.style.SUCCESS('\nSetup completed successfully!'))
        self.stdout.write('\nLogin credentials:')
        self.stdout.write('  Admin: admin@agroprice.com / admin123')
        self.stdout.write('  Business Head: businesshead@agroprice.com / bh123456')
        self.stdout.write('  Farmers: farmer1@agroprice.com, farmer2@agroprice.com, farmer3@agroprice.com / farmer123')
        self.stdout.write('  Buyers: buyer1@agroprice.com, buyer2@agroprice.com, buyer3@agroprice.com / buyer123')
