from django.core.management.base import BaseCommand
from core.models import MainCategory, Category, SubCategory, Item


class Command(BaseCommand):
    help = 'Load all product data for Kannammal Agro'

    def handle(self, *args, **options):
        self.stdout.write('Loading product data...')
        
        # Product data from the provided list
        products = [
            # Fresh Fruit - Apple N Pear
            ("Apple Amari", "Fresh Fruit", "Fruit N Vegetable", "Apple N Pear"),
            ("Apple Granny Smith", "Fresh Fruit", "Fruit N Vegetable", "Apple N Pear"),
            ("Apple Iran", "Fresh Fruit", "Fruit N Vegetable", "Apple N Pear"),
            ("Apple Kashmir Red Delicious", "Fresh Fruit", "Fruit N Vegetable", "Apple N Pear"),
            ("Apple Pink Lady", "Fresh Fruit", "Fruit N Vegetable", "Apple N Pear"),
            ("Apple Red Delicious", "Fresh Fruit", "Fruit N Vegetable", "Apple N Pear"),
            ("Apple Royal Gala", "Fresh Fruit", "Fruit N Vegetable", "Apple N Pear"),
            ("Apple Washington Red", "Fresh Fruit", "Fruit N Vegetable", "Apple N Pear"),
            ("Pear Green", "Fresh Fruit", "Fruit N Vegetable", "Apple N Pear"),
            ("Pear Red", "Fresh Fruit", "Fruit N Vegetable", "Apple N Pear"),
            
            # Fresh Fruit - Bananas
            ("Banana Karpooravalli", "Fresh Fruit", "Fruit N Vegetable", "Bananas"),
            ("Banana Nendran", "Fresh Fruit", "Fruit N Vegetable", "Bananas"),
            ("Banana Palayamthodan", "Fresh Fruit", "Fruit N Vegetable", "Bananas"),
            ("Banana Poovan", "Fresh Fruit", "Fruit N Vegetable", "Bananas"),
            ("Banana Red Kappa", "Fresh Fruit", "Fruit N Vegetable", "Bananas"),
            ("Banana Robusta Green", "Fresh Fruit", "Fruit N Vegetable", "Bananas"),
            ("Banana Robusta Yellow", "Fresh Fruit", "Fruit N Vegetable", "Bananas"),
            ("Banana Yellaki", "Fresh Fruit", "Fruit N Vegetable", "Bananas"),
            
            # Fresh Fruit - Temperate Fruit
            ("Guava White", "Fresh Fruit", "Fruit N Vegetable", "Temperate Fruit"),
            ("Guava Thailand", "Fresh Fruit", "Fruit N Vegetable", "Temperate Fruit"),
            
            # Fresh Fruit - Exotic Fruit
            ("Litchi", "Fresh Fruit", "Fruit N Vegetable", "Exotic Fruit"),
            
            # Fresh Fruit - Tropical Fruit
            ("Pine Apple", "Fresh Fruit", "Fruit N Vegetable", "Tropical Fruit"),
            ("Sapota Hybrid", "Fresh Fruit", "Fruit N Vegetable", "Tropical Fruit"),
            ("Ground Nut Fresh", "Fresh Fruit", "Fruit N Vegetable", "Tropical Fruit"),
            
            # Fresh Fruit - Regular Fruit
            ("Papaya", "Fresh Fruit", "Fruit N Vegetable", "Regular Fruit"),
            ("Dragon Fruit White", "Fresh Fruit", "Fruit N Vegetable", "Regular Fruit"),
            
            # Fresh Fruit - Seasonal Fruit
            ("Jujube Fruit", "Fresh Fruit", "Fruit N Vegetable", "Seasonal Fruit"),
            ("Golden Seethapazham", "Fresh Fruit", "Fruit N Vegetable", "Seasonal Fruit"),
            ("Grape Fruit", "Fresh Fruit", "Fruit N Vegetable", "Seasonal Fruit"),
            ("Persimmon", "Fresh Fruit", "Fruit N Vegetable", "Seasonal Fruit"),
            
            # Fresh Fruit - Pomegranate
            ("Pomegranate", "Fresh Fruit", "Fruit N Vegetable", "Pomegranate"),
            
            # Fresh Fruit - Citrus
            ("Indian Orange", "Fresh Fruit", "Fruit N Vegetable", "Citrus"),
            ("Mini Orange", "Fresh Fruit", "Fruit N Vegetable", "Citrus"),
            ("Mosambi", "Fresh Fruit", "Fruit N Vegetable", "Citrus"),
            ("Orange Imported", "Fresh Fruit", "Fruit N Vegetable", "Citrus"),
            ("Orange Kinnow Malta", "Fresh Fruit", "Fruit N Vegetable", "Citrus"),
            
            # Fresh Fruit - Melons
            ("Water Melon", "Fresh Fruit", "Fruit N Vegetable", "Melons"),
            ("Water Melon Kiran", "Fresh Fruit", "Fruit N Vegetable", "Melons"),
            ("Musk Melon", "Fresh Fruit", "Fruit N Vegetable", "Melons"),
            
            # Fresh Fruit - Grape
            ("Grapes Banglore Blue", "Fresh Fruit", "Fruit N Vegetable", "Grape"),
            ("Grapes Black Seedless", "Fresh Fruit", "Fruit N Vegetable", "Grape"),
            ("Grapes Green Imported", "Fresh Fruit", "Fruit N Vegetable", "Grape"),
            ("Grapes Panner", "Fresh Fruit", "Fruit N Vegetable", "Grape"),
            ("Grapes Sonaka Seedless", "Fresh Fruit", "Fruit N Vegetable", "Grape"),
            
            # Fresh Fruit - Mangoes
            ("Mango Kotturkonam", "Fresh Fruit", "Fruit N Vegetable", "Mangoes"),
            ("Mango Raw", "Fresh Fruit", "Fruit N Vegetable", "Mangoes"),
            ("Mango Raw Totapuri", "Fresh Fruit", "Fruit N Vegetable", "Mangoes"),
            
            # Fresh Fruit - Imported Fruit
            ("Grapes Imported", "Fresh Fruit", "Fruit N Vegetable", "Imported Fruit"),
            ("Plums Imported", "Fresh Fruit", "Fruit N Vegetable", "Imported Fruit"),
            ("Avacado Imported", "Fresh Fruit", "Fruit N Vegetable", "Imported Fruit"),
            
            # Fresh Fruit - Berries
            ("Blue Berry", "Fresh Fruit", "Fruit N Vegetable", "Berries"),
            ("Strawberry", "Fresh Fruit", "Fruit N Vegetable", "Berries"),
            
            # Fresh Fruit - Stone Fruit
            ("Avacado", "Fresh Fruit", "Fruit N Vegetable", "Stone Fruit"),
            
            # Fresh Fruit - Pre Cut Fruit Pack
            ("Cut Fruit Mix", "Fresh Fruit", "Fruit N Vegetable", "Pre Cut Fruit Pack"),
            ("Golden Kiwi Pack Of 3", "Fresh Fruit", "Fruit N Vegetable", "Pre Cut Fruit Pack"),
            ("Kiwi Pack Of 3", "Fresh Fruit", "Fruit N Vegetable", "Pre Cut Fruit Pack"),
            
            # Fresh Veg - Onion
            ("Onion Big", "Fresh Veg", "Fruit N Vegetable", "Onion"),
            ("Onion Sambar", "Fresh Veg", "Fruit N Vegetable", "Onion"),
            
            # Fresh Veg - Potato
            ("Baby Potato", "Fresh Veg", "Fruit N Vegetable", "Potato"),
            ("Potato Premium", "Fresh Veg", "Fruit N Vegetable", "Potato"),
            
            # Fresh Veg - Tomato
            ("Tomato Country", "Fresh Veg", "Fruit N Vegetable", "Tomato"),
            ("Tomato Hybrid", "Fresh Veg", "Fruit N Vegetable", "Tomato"),
            
            # Fresh Veg - Root Veg
            ("Beetroot", "Fresh Veg", "Fruit N Vegetable", "Root Veg"),
            ("Cabbage", "Fresh Veg", "Fruit N Vegetable", "Root Veg"),
            ("Carrot", "Fresh Veg", "Fruit N Vegetable", "Root Veg"),
            ("Radish White", "Fresh Veg", "Fruit N Vegetable", "Root Veg"),
            
            # Fresh Veg - Tropical Veg
            ("Banana Raw", "Fresh Veg", "Fruit N Vegetable", "Tropical Veg"),
            ("Banana Stem", "Fresh Veg", "Fruit N Vegetable", "Tropical Veg"),
            ("Capsicum Green", "Fresh Veg", "Fruit N Vegetable", "Tropical Veg"),
            ("Colacasia Big", "Fresh Veg", "Fruit N Vegetable", "Tropical Veg"),
            ("Colacasia Small", "Fresh Veg", "Fruit N Vegetable", "Tropical Veg"),
            ("Drum Stick", "Fresh Veg", "Fruit N Vegetable", "Tropical Veg"),
            ("Ginger Fresh", "Fresh Veg", "Fruit N Vegetable", "Tropical Veg"),
            ("Koorka", "Fresh Veg", "Fruit N Vegetable", "Tropical Veg"),
            ("Lemon", "Fresh Veg", "Fruit N Vegetable", "Tropical Veg"),
            ("Lemon Big", "Fresh Veg", "Fruit N Vegetable", "Tropical Veg"),
            ("Palm Sprouts", "Fresh Veg", "Fruit N Vegetable", "Tropical Veg"),
            ("Pumpkin", "Fresh Veg", "Fruit N Vegetable", "Tropical Veg"),
            ("Pumpkin Red", "Fresh Veg", "Fruit N Vegetable", "Tropical Veg"),
            ("Sweet Potato", "Fresh Veg", "Fruit N Vegetable", "Tropical Veg"),
            ("Tapioca", "Fresh Veg", "Fruit N Vegetable", "Tropical Veg"),
            ("Yam", "Fresh Veg", "Fruit N Vegetable", "Tropical Veg"),
            
            # Fresh Veg - Beans N Seed
            ("Beans Avarai Small", "Fresh Veg", "Fruit N Vegetable", "Beans N Seed"),
            ("Beans Cluster", "Fresh Veg", "Fruit N Vegetable", "Beans N Seed"),
            ("Beans Cowpea Long", "Fresh Veg", "Fruit N Vegetable", "Beans N Seed"),
            ("Beans Cowpea Small", "Fresh Veg", "Fruit N Vegetable", "Beans N Seed"),
            ("Beans French", "Fresh Veg", "Fruit N Vegetable", "Beans N Seed"),
            ("Beans Haricot", "Fresh Veg", "Fruit N Vegetable", "Beans N Seed"),
            ("Ladies Finger", "Fresh Veg", "Fruit N Vegetable", "Beans N Seed"),
            
            # Fresh Veg - Basic Veg
            ("Banana Flower", "Fresh Veg", "Fruit N Vegetable", "Basic Veg"),
            ("Banana Green Nendran", "Fresh Veg", "Fruit N Vegetable", "Basic Veg"),
            ("Brinjal Simran", "Fresh Veg", "Fruit N Vegetable", "Basic Veg"),
            ("Chilli Bhajji", "Fresh Veg", "Fruit N Vegetable", "Basic Veg"),
            ("Chilli Bullet", "Fresh Veg", "Fruit N Vegetable", "Basic Veg"),
            ("Chilli Green", "Fresh Veg", "Fruit N Vegetable", "Basic Veg"),
            ("Chilli Thondan", "Fresh Veg", "Fruit N Vegetable", "Basic Veg"),
            ("Cucumber English", "Fresh Veg", "Fruit N Vegetable", "Basic Veg"),
            ("Cucumber Madras", "Fresh Veg", "Fruit N Vegetable", "Basic Veg"),
            ("Cucumber Malabar", "Fresh Veg", "Fruit N Vegetable", "Basic Veg"),
            ("Cucumber Salad", "Fresh Veg", "Fruit N Vegetable", "Basic Veg"),
            ("Gooseberry", "Fresh Veg", "Fruit N Vegetable", "Basic Veg"),
            ("Sweet Tamarind", "Fresh Veg", "Fruit N Vegetable", "Basic Veg"),
            
            # Fresh Veg - Garlic
            ("Garlic Big", "Fresh Veg", "Fruit N Vegetable", "Garlic"),
            ("Garlic Himachal", "Fresh Veg", "Fruit N Vegetable", "Garlic"),
            ("Garlic Small", "Fresh Veg", "Fruit N Vegetable", "Garlic"),
            
            # Fresh Veg - Temperate Veg
            ("Brinjal Long Green", "Fresh Veg", "Fruit N Vegetable", "Temperate Veg"),
            ("Brinjal Nadan", "Fresh Veg", "Fruit N Vegetable", "Temperate Veg"),
            ("Brinjal Safal", "Fresh Veg", "Fruit N Vegetable", "Temperate Veg"),
            ("Brinjal Vari", "Fresh Veg", "Fruit N Vegetable", "Temperate Veg"),
            ("Brinjal White", "Fresh Veg", "Fruit N Vegetable", "Temperate Veg"),
            ("Chow Chow", "Fresh Veg", "Fruit N Vegetable", "Temperate Veg"),
            ("Coccinia", "Fresh Veg", "Fruit N Vegetable", "Temperate Veg"),
            
            # Fresh Veg - Coconut
            ("Coconut", "Fresh Veg", "Fruit N Vegetable", "Coconut"),
            
            # Fresh Veg - Exotic Veg
            ("Baby Corn Peeled", "Fresh Veg", "Fruit N Vegetable", "Exotic Veg"),
            ("Baby Corn Unpleed", "Fresh Veg", "Fruit N Vegetable", "Exotic Veg"),
            ("Broccoli", "Fresh Veg", "Fruit N Vegetable", "Exotic Veg"),
            ("Button Mushroom", "Fresh Veg", "Fruit N Vegetable", "Exotic Veg"),
            ("Cabbage Red", "Fresh Veg", "Fruit N Vegetable", "Exotic Veg"),
            ("Capsicum Red", "Fresh Veg", "Fruit N Vegetable", "Exotic Veg"),
            ("Capsicum Yellow", "Fresh Veg", "Fruit N Vegetable", "Exotic Veg"),
            ("Chinese Cabbage", "Fresh Veg", "Fruit N Vegetable", "Exotic Veg"),
            ("Lettuce Ice Berg", "Fresh Veg", "Fruit N Vegetable", "Exotic Veg"),
            ("Oyster Mushroom", "Fresh Veg", "Fruit N Vegetable", "Exotic Veg"),
            ("Zucchini Green", "Fresh Veg", "Fruit N Vegetable", "Exotic Veg"),
            ("Zucchini Yellow", "Fresh Veg", "Fruit N Vegetable", "Exotic Veg"),
            
            # Fresh Veg - Fresh Condiment
            ("American Sweet Corn", "Fresh Veg", "Fruit N Vegetable", "Fresh Condiment"),
            ("American Sweet Corn Pack Of 2", "Fresh Veg", "Fruit N Vegetable", "Fresh Condiment"),
            ("Green Peas", "Fresh Veg", "Fruit N Vegetable", "Fresh Condiment"),
            
            # Fresh Veg - Gourd
            ("Ash Gourd", "Fresh Veg", "Fruit N Vegetable", "Gourd"),
            ("Bitter Gourd Green", "Fresh Veg", "Fruit N Vegetable", "Gourd"),
            ("Bitter Gourd Nadan", "Fresh Veg", "Fruit N Vegetable", "Gourd"),
            ("Bitter Gourd White", "Fresh Veg", "Fruit N Vegetable", "Gourd"),
            ("Bottle Gourd", "Fresh Veg", "Fruit N Vegetable", "Gourd"),
            ("Ridge Gourd", "Fresh Veg", "Fruit N Vegetable", "Gourd"),
            ("Snake Gourd", "Fresh Veg", "Fruit N Vegetable", "Gourd"),
            ("Snake Gourd Long", "Fresh Veg", "Fruit N Vegetable", "Gourd"),
            ("Wax Gourd", "Fresh Veg", "Fruit N Vegetable", "Gourd"),
            
            # Fresh Veg - Leafy Veg
            ("Agathi Flower", "Fresh Veg", "Fruit N Vegetable", "Leafy Veg"),
            ("Agathi Keera", "Fresh Veg", "Fruit N Vegetable", "Leafy Veg"),
            ("Amaranthus Green", "Fresh Veg", "Fruit N Vegetable", "Leafy Veg"),
            ("Amaranthus Red", "Fresh Veg", "Fruit N Vegetable", "Leafy Veg"),
            ("Banana Leaves", "Fresh Veg", "Fruit N Vegetable", "Leafy Veg"),
            ("Corriander Leaves", "Fresh Veg", "Fruit N Vegetable", "Leafy Veg"),
            ("Curry Leaves", "Fresh Veg", "Fruit N Vegetable", "Leafy Veg"),
            ("Manathakkali Keerai", "Fresh Veg", "Fruit N Vegetable", "Leafy Veg"),
            ("Methi Leaves", "Fresh Veg", "Fruit N Vegetable", "Leafy Veg"),
            ("Mint Leaves", "Fresh Veg", "Fruit N Vegetable", "Leafy Veg"),
            ("Ponnanganni Keerai", "Fresh Veg", "Fruit N Vegetable", "Leafy Veg"),
            ("Spinach Palak Bunch", "Fresh Veg", "Fruit N Vegetable", "Leafy Veg"),
            
            # Fresh Veg - Exotic Leafy
            ("Celery", "Fresh Veg", "Fruit N Vegetable", "Exotic Leafy"),
            ("Leek", "Fresh Veg", "Fruit N Vegetable", "Exotic Leafy"),
            ("Spring Onion", "Fresh Veg", "Fruit N Vegetable", "Exotic Leafy"),
            
            # Fresh Veg - Pre Cut Veg
            ("Cut Veg", "Fresh Veg", "Fruit N Vegetable", "Pre Cut Veg"),
            ("Sambar Kit", "Fresh Veg", "Fruit N Vegetable", "Pre Cut Veg"),
            
            # Fresh Veg - Veg Flower
            ("Cauliflower", "Fresh Veg", "Fruit N Vegetable", "Veg Flower"),
            
            # Fresh Veg - Exotic Veg (Mushrooms)
            ("Milky Mushroom", "Fresh Veg", "Fruit N Vegetable", "Exotic Veg"),
        ]
        
        # Icons for categories
        category_icons = {
            'Fresh Fruit': '🍎',
            'Fresh Veg': '🥬',
        }
        
        # Icons for subcategories
        subcat_icons = {
            'Apple N Pear': '🍎',
            'Bananas': '🍌',
            'Temperate Fruit': '🍐',
            'Exotic Fruit': '🫐',
            'Tropical Fruit': '🍍',
            'Regular Fruit': '🍈',
            'Seasonal Fruit': '🍇',
            'Pomegranate': '🔴',
            'Citrus': '🍊',
            'Melons': '🍉',
            'Grape': '🍇',
            'Mangoes': '🥭',
            'Imported Fruit': '🍑',
            'Berries': '🍓',
            'Stone Fruit': '🥑',
            'Pre Cut Fruit Pack': '🥝',
            'Onion': '🧅',
            'Potato': '🥔',
            'Tomato': '🍅',
            'Root Veg': '🥕',
            'Tropical Veg': '🌶️',
            'Beans N Seed': '🫘',
            'Basic Veg': '🥒',
            'Garlic': '🧄',
            'Temperate Veg': '🍆',
            'Coconut': '🥥',
            'Exotic Veg': '🥦',
            'Fresh Condiment': '🌽',
            'Gourd': '🫛',
            'Leafy Veg': '🥬',
            'Exotic Leafy': '🌿',
            'Pre Cut Veg': '🥗',
            'Veg Flower': '🌸',
        }
        
        # Category colors
        category_colors = {
            'Fresh Fruit': '#ef4444',
            'Fresh Veg': '#22c55e',
        }
        
        # Create Main Category
        main_cat, _ = MainCategory.objects.get_or_create(
            name='Fruit N Vegetable',
            defaults={'icon': '🏪', 'description': 'Fresh Fruits and Vegetables'}
        )
        self.stdout.write(f'  Created/Found Main Category: {main_cat.name}')
        
        # Track created items
        categories_created = set()
        subcategories_created = set()
        items_created = 0
        items_in_list = set()  # Track all items in the new list
        
        for item_name, cat_name, main_cat_name, subcat_name in products:
            items_in_list.add(item_name)  # Add to tracking set
            # Create or get Category
            if cat_name not in categories_created:
                category, created = Category.objects.get_or_create(
                    name=cat_name,
                    defaults={
                        'main_category': main_cat,
                        'icon': category_icons.get(cat_name, '📦'),
                        'color': category_colors.get(cat_name, '#22c55e'),
                        'description': f'{cat_name} category'
                    }
                )
                if created:
                    categories_created.add(cat_name)
                    self.stdout.write(f'  Created Category: {cat_name}')
            else:
                category = Category.objects.get(name=cat_name)
            
            # Create or get SubCategory
            subcat_key = f"{cat_name}_{subcat_name}"
            if subcat_key not in subcategories_created:
                subcategory, created = SubCategory.objects.get_or_create(
                    category=category,
                    name=subcat_name,
                    defaults={
                        'icon': subcat_icons.get(subcat_name, '📦'),
                        'description': f'{subcat_name} subcategory'
                    }
                )
                if created:
                    subcategories_created.add(subcat_key)
                    self.stdout.write(f'    Created SubCategory: {subcat_name}')
            else:
                subcategory = SubCategory.objects.get(category=category, name=subcat_name)
            
            # Create Item
            item, created = Item.objects.get_or_create(
                subcategory=subcategory,
                name=item_name,
                defaults={
                    'unit': 'kg',
                    'description': f'{item_name}'
                }
            )
            if created:
                items_created += 1
        
        # Delete items not in the new list
        all_items = Item.objects.all()
        items_deleted = 0
        for item in all_items:
            if item.name not in items_in_list:
                self.stdout.write(f'  Deleting: {item.name}')
                item.delete()
                items_deleted += 1
        
        self.stdout.write(self.style.SUCCESS(
            f'\nSuccessfully loaded product data:\n'
            f'  - 1 Main Category\n'
            f'  - {len(categories_created)} Categories\n'
            f'  - {len(subcategories_created)} SubCategories\n'
            f'  - {items_created} Items created\n'
            f'  - {items_deleted} Items deleted'
        ))
