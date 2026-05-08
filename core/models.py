from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils import timezone


class UserManager(BaseUserManager):
    """Custom user manager for the custom User model"""
    
    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError('The Username field must be set')
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('role', 'admin')
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(username, password, **extra_fields)


class Region(models.Model):
    """Geographical regions for location-based access"""
    name = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100, default='India')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        unique_together = ['name', 'state']
    
    def __str__(self):
        return f"{self.name}, {self.state}"


class MainCategory(models.Model):
    """Main categories like Fruit N Vegetable"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    icon = models.CharField(max_length=50, default='🏪')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = 'Main Categories'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Category(models.Model):
    """Categories like Fresh Fruit, Fresh Veg"""
    main_category = models.ForeignKey(MainCategory, on_delete=models.CASCADE, related_name='categories', null=True, blank=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    icon = models.CharField(max_length=50, default='🍎')  # Emoji icon for cards
    color = models.CharField(max_length=20, default='#22c55e')  # Card color
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class SubCategory(models.Model):
    """Subcategories like Apple N Pear, Bananas, Onion etc."""
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='subcategories')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    icon = models.CharField(max_length=50, default='📦')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = 'Subcategories'
        ordering = ['category', 'name']
        unique_together = ['category', 'name']
    
    def __str__(self):
        return f"{self.category.name} - {self.name}"


class Item(models.Model):
    """Individual items/products like Apple Fuji, Banana Robusta etc."""
    subcategory = models.ForeignKey(SubCategory, on_delete=models.CASCADE, related_name='items')
    name = models.CharField(max_length=150)
    code = models.CharField(max_length=50, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    unit = models.CharField(max_length=20, default='kg')  # kg, piece, dozen, bunch etc.
    image = models.ImageField(upload_to='items/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = 'Items'
        ordering = ['subcategory', 'name']
        unique_together = ['subcategory', 'name']
    
    def __str__(self):
        return self.name


class Store(models.Model):
    """Store entity - represents physical stores"""
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50, unique=True)
    address = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Store'
        verbose_name_plural = 'Stores'
    
    def __str__(self):
        return f"{self.name} ({self.code})"


class Farmer(models.Model):
    """Farmer/Shop entity - represents actual farmers whose prices are collected"""
    name = models.CharField(max_length=200)  # Farmer or Shop name
    phone = models.CharField(max_length=15, blank=True, null=True)
    region = models.ForeignKey(Region, on_delete=models.SET_NULL, null=True, blank=True, related_name='farmers')
    address = models.TextField(blank=True, null=True)
    shop_name = models.CharField(max_length=200, blank=True, null=True)  # Optional shop name if different
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Farmer'
        verbose_name_plural = 'Farmers'
    
    def __str__(self):
        location = f" - {self.region.name}" if self.region else ""
        return f"{self.name}{location}"


class User(AbstractUser):
    """Custom User model with roles and permissions"""
    
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('business_head', 'Business Head'),
        ('farmer', 'Farmer'),
        ('buyer', 'Buyer'),
        ('store_manager', 'Store Manager'),
        ('team_leader', 'Team Leader'),
        ('store_head', 'Store Head'),
    ]
    
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='buyer')
    region = models.ForeignKey(Region, on_delete=models.SET_NULL, null=True, blank=True, related_name='users')
    assigned_store = models.ForeignKey('Store', on_delete=models.SET_NULL, null=True, blank=True, related_name='managers')
    managed_stores = models.ManyToManyField('Store', blank=True, related_name='store_heads')
    profile_image = models.ImageField(upload_to='profiles/', blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    company_name = models.CharField(max_length=200, blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    has_direct_access = models.BooleanField(default=False)  # For farmers with direct access
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Granular permissions - categories this user can access
    allowed_categories = models.ManyToManyField(Category, blank=True, related_name='allowed_users')
    
    # Farmers assigned to this buyer for price collection
    assigned_farmers = models.ManyToManyField('Farmer', blank=True, related_name='assigned_buyers')
    
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    objects = UserManager()
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.username})"
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.username
    
    def can_access_category(self, category):
        """Check if user can access a specific category"""
        if self.role == 'admin' or self.role == 'business_head':
            return True
        return category in self.allowed_categories.all()
    
    def can_enter_price(self):
        """Check if user can enter prices"""
        return self.role in ['farmer', 'buyer'] and (self.has_direct_access or self.role == 'buyer')


class UserCategoryPermission(models.Model):
    """Granular permission for user-category-subcategory-item access"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='category_permissions')
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    subcategories = models.ManyToManyField(SubCategory, blank=True)
    items = models.ManyToManyField(Item, blank=True)  # Granular item-level permissions
    can_view = models.BooleanField(default=True)
    can_edit_price = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user', 'category']
        verbose_name = 'User Category Permission'
        verbose_name_plural = 'User Category Permissions'
    
    def __str__(self):
        return f"{self.user.email} - {self.category.name}"


class PriceEntry(models.Model):
    """Price entries by farmers and buyers"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='price_entries')
    farmer = models.ForeignKey('Farmer', on_delete=models.SET_NULL, null=True, blank=True, related_name='price_entries')
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='price_entries', null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField(default=timezone.now)
    notes = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    # Approval fields
    is_approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_prices')
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date', '-created_at']
        verbose_name = 'Price Entry'
        verbose_name_plural = 'Price Entries'
    
    def __str__(self):
        item_name = self.item.name if self.item else 'Unknown'
        farmer_name = f" from {self.farmer.name}" if self.farmer else ""
        return f"{item_name} - ₹{self.price}{farmer_name} by {self.user.get_full_name()} on {self.date}"

class Notification(models.Model):
    """Notifications for users"""
    NOTIFICATION_TYPES = [
        ('price_approved', 'Price Approved'),
        ('price_rejected', 'Price Rejected'),
        ('general', 'General'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES, default='general')
    title = models.CharField(max_length=200)
    message = models.TextField()
    price_entry = models.ForeignKey(PriceEntry, on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
    
    def __str__(self):
        return f"{self.title} - {self.user.get_full_name()}"


class ItemRating(models.Model):
    """Item ratings by store managers"""
    RATING_CHOICES = [
        (-1, 'N/A - Not Available'),
        (0, '0 - Poor'),
        (5, '5 - Average'),
        (10, '10 - Excellent'),
    ]
    
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='ratings')
    store = models.ForeignKey('Store', on_delete=models.CASCADE, related_name='item_ratings')
    store_manager = models.ForeignKey(User, on_delete=models.CASCADE, related_name='item_ratings')
    rating = models.IntegerField(choices=RATING_CHOICES)
    photo = models.ImageField(upload_to='ratings/%Y/%m/%d/', blank=True, null=True)
    comment = models.TextField(blank=True, null=True)
    rated_date = models.DateField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-rated_date', '-created_at']
        verbose_name = 'Item Rating'
        verbose_name_plural = 'Item Ratings'
        unique_together = ['item', 'store', 'store_manager', 'rated_date']
    
    def __str__(self):
        return f"{self.item.name} - {self.store.name} - {self.rating}/10 on {self.rated_date}"


class ActivityLog(models.Model):
    """Track user activities for audit"""
    ACTION_CHOICES = [
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('price_add', 'Price Added'),
        ('price_update', 'Price Updated'),
        ('category_view', 'Category Viewed'),
        ('user_create', 'User Created'),
        ('user_update', 'User Updated'),
        ('permission_change', 'Permission Changed'),
        ('rating_add', 'Rating Added'),
        ('rating_update', 'Rating Updated'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    description = models.TextField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Activity Log'
        verbose_name_plural = 'Activity Logs'
    
    def __str__(self):
        return f"{self.user.email} - {self.action} at {self.created_at}"

