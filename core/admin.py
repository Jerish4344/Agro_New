from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Region, MainCategory, Category, SubCategory, Item, PriceEntry, UserCategoryPermission, ActivityLog, Farmer, Store, ItemRating


@admin.register(Farmer)
class FarmerAdmin(admin.ModelAdmin):
    list_display = ['name', 'shop_name', 'region', 'phone', 'is_active', 'created_at']
    list_filter = ['region', 'is_active']
    search_fields = ['name', 'shop_name', 'phone', 'address']
    ordering = ['name']


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name', 'code', 'address']
    ordering = ['name']


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'first_name', 'last_name', 'role', 'region', 'assigned_store', 'is_active', 'has_direct_access']
    list_filter = ['role', 'is_active', 'region', 'has_direct_access', 'assigned_store']
    search_fields = ['email', 'first_name', 'last_name', 'company_name']
    ordering = ['-created_at']
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'phone', 'address', 'company_name', 'profile_image')}),
        ('Role & Access', {'fields': ('role', 'region', 'assigned_store', 'managed_stores', 'has_direct_access', 'is_verified', 'allowed_categories', 'assigned_farmers')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'role', 'password1', 'password2'),
        }),
    )
    
    filter_horizontal = ['managed_stores', 'allowed_categories', 'assigned_farmers', 'groups', 'user_permissions']

@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ['name', 'state', 'country', 'is_active']
    list_filter = ['state', 'country', 'is_active']
    search_fields = ['name', 'state']


@admin.register(MainCategory)
class MainCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'main_category', 'icon', 'is_active', 'created_at']
    list_filter = ['main_category', 'is_active']
    search_fields = ['name', 'main_category__name']


@admin.register(SubCategory)
class SubCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'is_active']
    list_filter = ['category', 'is_active']
    search_fields = ['name', 'category__name']


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'subcategory', 'unit', 'is_active']
    list_filter = ['subcategory__category', 'is_active']
    search_fields = ['name', 'code', 'subcategory__name']


@admin.register(PriceEntry)
class PriceEntryAdmin(admin.ModelAdmin):
    list_display = ['item', 'farmer', 'user', 'price', 'date', 'created_at']
    list_filter = ['item__subcategory__category', 'farmer', 'date', 'user__role']
    search_fields = ['item__name', 'user__email', 'farmer__name']
    date_hierarchy = 'date'


@admin.register(UserCategoryPermission)
class UserCategoryPermissionAdmin(admin.ModelAdmin):
    list_display = ['user', 'category', 'can_view', 'can_edit_price']
    list_filter = ['category', 'can_view', 'can_edit_price']
    search_fields = ['user__email', 'category__name']
    filter_horizontal = ['subcategories', 'items']


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'created_at', 'ip_address']
    list_filter = ['action', 'created_at']
    search_fields = ['user__email', 'description']
    date_hierarchy = 'created_at'


@admin.register(ItemRating)
class ItemRatingAdmin(admin.ModelAdmin):
    list_display = ['item', 'store', 'store_manager', 'rating', 'rated_date', 'created_at']
    list_filter = ['store', 'rating', 'rated_date', 'item__subcategory__category']
    search_fields = ['item__name', 'store__name', 'store_manager__email', 'comment']
    date_hierarchy = 'rated_date'
    ordering = ['-rated_date', '-created_at']
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('item', 'store', 'store_manager')

