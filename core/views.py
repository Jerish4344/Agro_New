from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Min, Q
from django.utils import timezone
from datetime import datetime, timedelta
from collections import defaultdict
import json

from .models import (
    User, Category, SubCategory, Region, PriceEntry, 
    UserCategoryPermission, ActivityLog, MainCategory, Item, Farmer, Notification, Store, ItemRating
)
from .forms import (
    LoginForm, UserRegistrationForm, UserEditForm, CategoryForm, 
    SubCategoryForm, RegionForm, PriceEntryForm, UserCategoryPermissionForm, FarmerForm, StoreManagerForm, TeamLeaderForm, StoreForm, StoreHeadForm
)
from .decorators import role_required, admin_required, business_head_required, admin_or_business_head_required, store_manager_required, store_staff_required, reports_access_required


def login_view(request):
    """User login view"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            
            # Log activity
            ActivityLog.objects.create(
                user=user,
                action='login',
                description=f'User logged in from {get_client_ip(request)}',
                ip_address=get_client_ip(request)
            )
            
            messages.success(request, f'Welcome back, {user.get_full_name()}!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = LoginForm()
    
    return render(request, 'core/login.html', {'form': form})


@login_required
def logout_view(request):
    """User logout view"""
    ActivityLog.objects.create(
        user=request.user,
        action='logout',
        description='User logged out',
        ip_address=get_client_ip(request)
    )
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('login')


@login_required
def dashboard(request):
    """Main dashboard view - shows categories as cards"""
    user = request.user
    
    # Get categories based on user role
    if user.role in ['admin', 'business_head']:
        categories = Category.objects.filter(is_active=True)
    else:
        # Get categories the user has permission to access
        permitted_category_ids = UserCategoryPermission.objects.filter(
            user=user, can_view=True
        ).values_list('category_id', flat=True)
        categories = Category.objects.filter(
            Q(id__in=permitted_category_ids) | Q(id__in=user.allowed_categories.all()),
            is_active=True
        ).distinct()
    
    # Calculate accessible subcategory count for each category
    categories_with_counts = []
    for category in categories:
        if user.role in ['admin', 'business_head']:
            # Admin and Business Head can see all subcategories
            accessible_subcategory_count = category.subcategories.filter(is_active=True).count()
        else:
            # Check user's specific permissions for this category
            permission = UserCategoryPermission.objects.filter(user=user, category=category).first()
            if permission and permission.subcategories.exists():
                # User has specific subcategory permissions - count only those
                accessible_subcategory_count = permission.subcategories.filter(is_active=True).count()
            elif user.has_direct_access or category in user.allowed_categories.all():
                # User has direct/full access to category - show all subcategories
                accessible_subcategory_count = category.subcategories.filter(is_active=True).count()
            else:
                accessible_subcategory_count = 0
        
        # Add the count as an attribute to the category object
        category.accessible_subcategory_count = accessible_subcategory_count
        categories_with_counts.append(category)
    
    # Get statistics for admin/business_head
    stats = {}
    if user.role in ['admin', 'business_head']:
        stats = {
            'total_users': User.objects.count(),
            'total_categories': Category.objects.filter(is_active=True).count(),
            'total_subcategories': SubCategory.objects.filter(is_active=True).count(),
            'total_items': Item.objects.filter(is_active=True).count(),
            'today_entries': PriceEntry.objects.filter(date=timezone.now().date()).count(),
            'total_farmers': User.objects.filter(role='farmer').count(),
            'total_buyers': User.objects.filter(role='buyer').count(),
        }
    
    context = {
        'categories': categories_with_counts,
        'stats': stats,
    }
    return render(request, 'core/dashboard.html', context)


@login_required
def category_detail(request, category_id):
    """View category with subcategories and items with prices in excel format"""
    category = get_object_or_404(Category, id=category_id, is_active=True)
    user = request.user
    
    # Check permission
    if user.role not in ['admin', 'business_head']:
        has_permission = UserCategoryPermission.objects.filter(
            user=user, category=category, can_view=True
        ).exists() or category in user.allowed_categories.all()
        
        if not has_permission:
            messages.error(request, 'You do not have permission to view this category.')
            return redirect('dashboard')
    
    # Log activity
    ActivityLog.objects.create(
        user=user,
        action='category_view',
        description=f'Viewed category: {category.name}',
        ip_address=get_client_ip(request)
    )
    
    # Get subcategories based on user role and permissions
    if user.role in ['admin', 'business_head']:
        # Admin and Business Head can see all subcategories
        subcategories = category.subcategories.filter(is_active=True).prefetch_related('items')
    else:
        # Farmers and Buyers can only see subcategories they have permission for
        permission = UserCategoryPermission.objects.filter(user=user, category=category).first()
        if permission and permission.subcategories.exists():
            # User has specific subcategory permissions
            subcategories = permission.subcategories.filter(is_active=True).prefetch_related('items')
        else:
            # If no specific subcategories assigned, show all (fallback for has_direct_access users)
            if user.has_direct_access:
                subcategories = category.subcategories.filter(is_active=True).prefetch_related('items')
            else:
                # No permission - show empty
                subcategories = SubCategory.objects.none()
    
    # Get items based on permissions
    if user.role in ['admin', 'business_head']:
        items = Item.objects.filter(subcategory__in=subcategories, is_active=True)
    else:
        permission = UserCategoryPermission.objects.filter(user=user, category=category).first()
        if permission and permission.items.exists():
            # User has specific item permissions
            items = permission.items.filter(is_active=True)
        else:
            # Show all items from permitted subcategories
            items = Item.objects.filter(subcategory__in=subcategories, is_active=True)
    
    # Calculate accessible item count for each subcategory
    subcategories_with_counts = []
    for subcategory in subcategories:
        if user.role in ['admin', 'business_head']:
            # Admin and Business Head can see all items
            accessible_item_count = subcategory.items.filter(is_active=True).count()
        else:
            permission = UserCategoryPermission.objects.filter(user=user, category=category).first()
            if permission and permission.items.exists():
                # User has specific item permissions - count only permitted items in this subcategory
                accessible_item_count = permission.items.filter(subcategory=subcategory, is_active=True).count()
            else:
                # No specific item restrictions - show all items in subcategory
                accessible_item_count = subcategory.items.filter(is_active=True).count()
        
        subcategory.accessible_item_count = accessible_item_count
        subcategories_with_counts.append(subcategory)
    
    # Get date range for price display (last 30 days)
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)
    
    # Check which subcategories have recent prices and sort them
    for subcategory in subcategories_with_counts:
        # Get items for this subcategory
        subcat_items = Item.objects.filter(subcategory=subcategory, is_active=True)
        # Check if there are any recent prices for these items
        has_prices = PriceEntry.objects.filter(
            item__in=subcat_items,
            date__gte=start_date,
            date__lte=end_date,
            is_active=True
        ).exists()
        subcategory.has_recent_prices = has_prices
    
    # Sort subcategories: those with prices first, then alphabetically by name
    subcategories_with_counts = sorted(
        subcategories_with_counts,
        key=lambda x: (not x.has_recent_prices, x.name.lower())
    )
    
    # Get all dates in range
    dates = []
    current_date = start_date
    while current_date <= end_date:
        dates.append(current_date)
        current_date += timedelta(days=1)
    
    # Determine if user can see all prices (Admin/Business Head) or only their own (Farmer/Buyer)
    can_see_all_prices = user.role in ['admin', 'business_head']
    
    # Get price entries based on user role
    if can_see_all_prices:
        # Admin and Business Head can see ALL prices from all users
        price_entries = PriceEntry.objects.filter(
            item__in=items,
            date__gte=start_date,
            date__lte=end_date,
            is_active=True
        ).select_related('item', 'user', 'farmer')
    else:
        # Farmers and Buyers can only see their OWN prices
        price_entries = PriceEntry.objects.filter(
            item__in=items,
            date__gte=start_date,
            date__lte=end_date,
            is_active=True,
            user=user  # Only show current user's prices
        ).select_related('item', 'user', 'farmer')
    
    # Organize data for excel-like display
    # Structure: {date: {item_id: [{user, farmer, price, is_lowest}, ...]}}
    price_data = defaultdict(lambda: defaultdict(list))
    
    # Get minimum price per item per date (from ALL entries for comparison)
    # This is only used for Admin/Business Head view
    min_prices = {}
    if can_see_all_prices:
        all_entries_for_min = PriceEntry.objects.filter(
            item__in=items,
            date__gte=start_date,
            date__lte=end_date,
            is_active=True
        )
        for entry in all_entries_for_min:
            key = (entry.date, entry.item_id)
            if key not in min_prices or entry.price < min_prices[key]:
                min_prices[key] = entry.price
    
    # Build price data with lowest price marked (only for admin/business_head)
    for entry in price_entries:
        key = (entry.date, entry.item_id)
        is_lowest = False
        if can_see_all_prices:
            is_lowest = entry.price == min_prices.get(key, None)
        price_data[entry.date][entry.item_id].append({
            'user': entry.user,
            'farmer': entry.farmer,
            'price': entry.price,
            'is_lowest': is_lowest,
            'notes': entry.notes,
            'id': entry.id
        })
    
    # Check if user can enter prices
    can_enter_price = False
    if user.role in ['farmer', 'buyer']:
        permission = UserCategoryPermission.objects.filter(
            user=user, category=category, can_edit_price=True
        ).first()
        can_enter_price = permission is not None or user.has_direct_access
    
    context = {
        'category': category,
        'subcategories': subcategories_with_counts,
        'items': items,
        'dates': dates,
        'price_data': dict(price_data),
        'can_enter_price': can_enter_price,
        'can_see_all_prices': can_see_all_prices,
        'today': timezone.now().date(),
    }
    return render(request, 'core/category_detail.html', context)


@login_required
def subcategory_detail(request, category_id, subcategory_id):
    """View subcategory with items and their prices"""
    category = get_object_or_404(Category, id=category_id, is_active=True)
    subcategory = get_object_or_404(SubCategory, id=subcategory_id, category=category, is_active=True)
    user = request.user
    
    # Check permission
    if user.role not in ['admin', 'business_head']:
        has_permission = UserCategoryPermission.objects.filter(
            user=user, category=category, can_view=True
        ).exists() or category in user.allowed_categories.all()
        
        if not has_permission:
            messages.error(request, 'You do not have permission to view this category.')
            return redirect('dashboard')
    
    # Get items based on permissions
    if user.role in ['admin', 'business_head']:
        items = Item.objects.filter(subcategory=subcategory, is_active=True).order_by('name')
    else:
        permission = UserCategoryPermission.objects.filter(user=user, category=category).first()
        if permission and permission.items.exists():
            items = permission.items.filter(subcategory=subcategory, is_active=True).order_by('name')
        else:
            items = Item.objects.filter(subcategory=subcategory, is_active=True).order_by('name')
    
    # Get date range for price display (last 30 days)
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)
    
    # Get all dates in range
    dates = []
    current_date = start_date
    while current_date <= end_date:
        dates.append(current_date)
        current_date += timedelta(days=1)
    
    # Determine if user can see all prices
    can_see_all_prices = user.role in ['admin', 'business_head']
    
    # Get price entries
    if can_see_all_prices:
        price_entries = PriceEntry.objects.filter(
            item__in=items,
            date__gte=start_date,
            date__lte=end_date,
            is_active=True
        ).select_related('item', 'user', 'farmer')
    else:
        price_entries = PriceEntry.objects.filter(
            item__in=items,
            date__gte=start_date,
            date__lte=end_date,
            is_active=True,
            user=user
        ).select_related('item', 'user', 'farmer')
    
    # Organize price data
    price_data = defaultdict(lambda: defaultdict(list))
    min_prices = {}
    
    if can_see_all_prices:
        all_entries_for_min = PriceEntry.objects.filter(
            item__in=items,
            date__gte=start_date,
            date__lte=end_date,
            is_active=True
        )
        for entry in all_entries_for_min:
            key = (entry.date, entry.item_id)
            if key not in min_prices or entry.price < min_prices[key]:
                min_prices[key] = entry.price
    
    for entry in price_entries:
        key = (entry.date, entry.item_id)
        is_lowest = False
        if can_see_all_prices:
            is_lowest = entry.price == min_prices.get(key, None)
        price_data[entry.date][entry.item_id].append({
            'user': entry.user,
            'farmer': entry.farmer,
            'price': entry.price,
            'is_lowest': is_lowest,
            'notes': entry.notes,
            'id': entry.id,
            'is_approved': entry.is_approved,
            'approved_by': entry.approved_by
        })
    
    # Check if user can enter prices
    can_enter_price = False
    if user.role in ['farmer', 'buyer']:
        permission = UserCategoryPermission.objects.filter(
            user=user, category=category, can_edit_price=True
        ).first()
        can_enter_price = permission is not None or user.has_direct_access
    
    context = {
        'category': category,
        'subcategory': subcategory,
        'items': items,
        'dates': dates,
        'price_data': dict(price_data),
        'can_enter_price': can_enter_price,
        'can_see_all_prices': can_see_all_prices,
        'today': timezone.now().date(),
    }
    return render(request, 'core/subcategory_detail.html', context)


@login_required
def enter_price(request, category_id, subcategory_id=None):
    """View to enter prices for a category or specific subcategory"""
    category = get_object_or_404(Category, id=category_id, is_active=True)
    user = request.user
    
    # Get the specific subcategory if provided
    selected_subcategory = None
    if subcategory_id:
        selected_subcategory = get_object_or_404(SubCategory, id=subcategory_id, category=category, is_active=True)
    
    # Check permission
    if user.role not in ['admin']:
        permission = UserCategoryPermission.objects.filter(
            user=user, category=category, can_edit_price=True
        ).first()
        
        if not permission and not user.has_direct_access:
            messages.error(request, 'You do not have permission to enter prices for this category.')
            return redirect('category_detail', category_id=category_id)
    
    # Get farmers assigned to this user (for buyers)
    # Admin can see all farmers, buyers can only see their assigned farmers
    if user.role == 'admin':
        available_farmers = Farmer.objects.filter(is_active=True).order_by('name')
    else:
        available_farmers = user.assigned_farmers.filter(is_active=True).order_by('name')
    
    # Get selected farmer from query param or POST
    selected_farmer = None
    farmer_id = request.GET.get('farmer_id') or request.POST.get('farmer_id')
    if farmer_id:
        try:
            if user.role == 'admin':
                selected_farmer = Farmer.objects.get(id=farmer_id, is_active=True)
            else:
                selected_farmer = user.assigned_farmers.get(id=farmer_id, is_active=True)
        except Farmer.DoesNotExist:
            pass
    
    # Get subcategories and their items
    subcategories = category.subcategories.filter(is_active=True).prefetch_related('items')
    
    # Get user's permitted items
    if user.role == 'admin':
        # Admin can see all items
        items = Item.objects.filter(
            subcategory__category=category,
            subcategory__is_active=True,
            is_active=True
        ).select_related('subcategory').order_by('subcategory__name', 'name')
    else:
        permission = UserCategoryPermission.objects.filter(user=user, category=category).first()
        if permission and permission.items.exists():
            items = permission.items.filter(is_active=True).select_related('subcategory').order_by('subcategory__name', 'name')
        else:
            # Default to all items if no specific permission
            items = Item.objects.filter(
                subcategory__category=category,
                subcategory__is_active=True,
                is_active=True
            ).select_related('subcategory').order_by('subcategory__name', 'name')
    
    # Filter by selected subcategory if provided
    if selected_subcategory:
        items = items.filter(subcategory=selected_subcategory)
    
    if request.method == 'POST':
        date = request.POST.get('date', timezone.now().date())
        if isinstance(date, str):
            date = datetime.strptime(date, '%Y-%m-%d').date()
        
        # Get the farmer from POST (required for buyers)
        post_farmer_id = request.POST.get('farmer_id')
        post_farmer = None
        if post_farmer_id:
            try:
                if user.role == 'admin':
                    post_farmer = Farmer.objects.get(id=post_farmer_id, is_active=True)
                else:
                    post_farmer = user.assigned_farmers.get(id=post_farmer_id, is_active=True)
            except Farmer.DoesNotExist:
                messages.error(request, 'Invalid farmer selected.')
                return redirect('category_detail', category_id=category_id)
        
        # For buyers, farmer is required
        if user.role == 'buyer' and not post_farmer:
            messages.error(request, 'Please select a farmer before entering prices.')
            return redirect(request.path)
        
        prices_added = 0
        for item in items:
            price_value = request.POST.get(f'price_{item.id}')
            if price_value:
                try:
                    price = float(price_value)
                    # Include farmer in the unique constraint for price entry
                    obj, created = PriceEntry.objects.update_or_create(
                        user=user,
                        farmer=post_farmer,
                        item=item,
                        date=date,
                        defaults={'price': price, 'is_active': True}
                    )
                    prices_added += 1
                    
                    # Log activity
                    action = 'price_add' if created else 'price_update'
                    farmer_info = f' from {post_farmer.name}' if post_farmer else ''
                    ActivityLog.objects.create(
                        user=user,
                        action=action,
                        description=f'{"Added" if created else "Updated"} price for {item.name}: ₹{price}{farmer_info}',
                        ip_address=get_client_ip(request)
                    )
                except ValueError:
                    pass
        
        if prices_added > 0:
            messages.success(request, f'Successfully saved {prices_added} price entries.')
        return redirect('category_detail', category_id=category_id)
    
    # Get existing prices for today (for the selected farmer if any)
    today_prices = {}
    price_filter = {
        'user': user,
        'item__in': items,
        'date': timezone.now().date()
    }
    if selected_farmer:
        price_filter['farmer'] = selected_farmer
    
    existing_entries = PriceEntry.objects.filter(**price_filter)
    for entry in existing_entries:
        today_prices[entry.item_id] = entry.price
    
    # Group items by subcategory for display
    items_by_subcategory = {}
    for item in items:
        if item.subcategory not in items_by_subcategory:
            items_by_subcategory[item.subcategory] = []
        items_by_subcategory[item.subcategory].append(item)
    
    context = {
        'category': category,
        'subcategories': subcategories,
        'selected_subcategory': selected_subcategory,
        'available_farmers': available_farmers,
        'selected_farmer': selected_farmer,
        'items': items,
        'items_by_subcategory': items_by_subcategory,
        'today_prices': today_prices,
        'today': timezone.now().date(),
    }
    return render(request, 'core/enter_price.html', context)


@login_required
def category_price_history(request, category_id):
    """View detailed price history for a category in table format"""
    category = get_object_or_404(Category, id=category_id, is_active=True)
    user = request.user
    
    # Check permission
    if user.role not in ['admin', 'business_head']:
        has_permission = UserCategoryPermission.objects.filter(
            user=user, category=category, can_view=True
        ).exists() or category in user.allowed_categories.all()
        
        if not has_permission:
            messages.error(request, 'You do not have permission to view this category.')
            return redirect('dashboard')
    
    # Get subcategories and items based on permissions
    if user.role in ['admin', 'business_head']:
        subcategories = category.subcategories.filter(is_active=True).prefetch_related('items')
        items = Item.objects.filter(subcategory__in=subcategories, is_active=True).order_by('subcategory__name', 'name')
    else:
        permission = UserCategoryPermission.objects.filter(user=user, category=category).first()
        if permission and permission.items.exists():
            items = permission.items.filter(is_active=True).order_by('subcategory__name', 'name')
        else:
            subcategories = category.subcategories.filter(is_active=True)
            items = Item.objects.filter(subcategory__in=subcategories, is_active=True).order_by('subcategory__name', 'name')
        subcategories = category.subcategories.filter(is_active=True)
    
    # Get date range for price display (last 30 days)
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)
    
    # Get all dates in range
    dates = []
    current_date = start_date
    while current_date <= end_date:
        dates.append(current_date)
        current_date += timedelta(days=1)
    
    # Determine if user can see all prices
    can_see_all_prices = user.role in ['admin', 'business_head']
    
    # Get price entries
    if can_see_all_prices:
        price_entries = PriceEntry.objects.filter(
            item__in=items,
            date__gte=start_date,
            date__lte=end_date,
            is_active=True
        ).select_related('item', 'user')
    else:
        price_entries = PriceEntry.objects.filter(
            item__in=items,
            date__gte=start_date,
            date__lte=end_date,
            is_active=True,
            user=user
        ).select_related('item', 'user')
    
    # Organize data for table display
    price_data = defaultdict(lambda: defaultdict(list))
    
    # Get minimum price per item per date
    min_prices = {}
    if can_see_all_prices:
        all_entries_for_min = PriceEntry.objects.filter(
            item__in=items,
            date__gte=start_date,
            date__lte=end_date,
            is_active=True
        )
        for entry in all_entries_for_min:
            key = (entry.date, entry.item_id)
            if key not in min_prices or entry.price < min_prices[key]:
                min_prices[key] = entry.price
    
    # Build price data
    for entry in price_entries:
        key = (entry.date, entry.item_id)
        is_lowest = False
        if can_see_all_prices:
            is_lowest = entry.price == min_prices.get(key, None)
        price_data[entry.date][entry.item_id].append({
            'user': entry.user,
            'price': entry.price,
            'is_lowest': is_lowest,
            'notes': entry.notes,
            'id': entry.id
        })
    
    context = {
        'category': category,
        'subcategories': subcategories,
        'items': items,
        'dates': dates,
        'price_data': dict(price_data),
        'can_see_all_prices': can_see_all_prices,
        'today': timezone.now().date(),
    }
    return render(request, 'core/category_price_history.html', context)


# ============ Admin Views ============

@login_required
@admin_or_business_head_required
def admin_dashboard(request):
    """Admin dashboard with all management options"""
    stats = {
        'total_users': User.objects.count(),
        'active_users': User.objects.filter(is_active=True).count(),
        'total_main_categories': MainCategory.objects.count(),
        'total_categories': Category.objects.count(),
        'total_subcategories': SubCategory.objects.count(),
        'total_items': Item.objects.count(),
        'total_regions': Region.objects.count(),
        'total_price_entries': PriceEntry.objects.count(),
        'today_entries': PriceEntry.objects.filter(date=timezone.now().date()).count(),
        'farmers': User.objects.filter(role='farmer').count(),
        'buyers': User.objects.filter(role='buyer').count(),
        'business_heads': User.objects.filter(role='business_head').count(),
    }
    
    # Recent activities
    recent_activities = ActivityLog.objects.select_related('user')[:20]
    
    context = {
        'stats': stats,
        'recent_activities': recent_activities,
    }
    return render(request, 'core/admin/dashboard.html', context)


@login_required
@admin_or_business_head_required
def user_list(request):
    """List all users"""
    current_user = request.user
    users = User.objects.all().select_related('region')
    
    # Business Head can only see farmers and buyers (not admin or other business_heads)
    if current_user.role == 'business_head':
        users = users.filter(role__in=['farmer', 'buyer'])
    
    # Filters
    role = request.GET.get('role')
    region = request.GET.get('region')
    search = request.GET.get('search')
    
    if role:
        users = users.filter(role=role)
    if region:
        users = users.filter(region_id=region)
    if search:
        users = users.filter(
            Q(email__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(company_name__icontains=search)
        )
    
    regions = Region.objects.filter(is_active=True)
    
    # Restrict role choices for business_head
    if current_user.role == 'business_head':
        role_choices = [r for r in User.ROLE_CHOICES if r[0] in ['farmer', 'buyer']]
    else:
        role_choices = User.ROLE_CHOICES
    
    context = {
        'users': users,
        'regions': regions,
        'roles': role_choices,
        'current_role': role,
        'current_region': region,
        'search': search or '',
        'is_business_head': current_user.role == 'business_head',
    }
    return render(request, 'core/admin/user_list.html', context)


@login_required
@admin_or_business_head_required
def user_create(request):
    """Create a new user"""
    current_user = request.user
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        
        # Business Head can only create farmers and buyers
        if current_user.role == 'business_head':
            role = request.POST.get('role')
            if role in ['admin', 'business_head']:
                messages.error(request, 'You can only create farmers and buyers.')
                return redirect('user_create')
        
        if form.is_valid():
            user = form.save()
            
            # Log activity
            ActivityLog.objects.create(
                user=request.user,
                action='user_create',
                description=f'Created user: {user.email}',
                ip_address=get_client_ip(request)
            )
            
            messages.success(request, f'User {user.email} created successfully.')
            return redirect('user_permissions', user_id=user.id)
    else:
        form = UserRegistrationForm()
    
    # Restrict role choices for business_head
    if current_user.role == 'business_head':
        form.fields['role'].choices = [r for r in User.ROLE_CHOICES if r[0] in ['farmer', 'buyer']]
    
    return render(request, 'core/admin/user_form.html', {
        'form': form,
        'title': 'Create User',
        'action': 'Create'
    })


@login_required
@admin_or_business_head_required
def user_edit(request, user_id):
    """Edit a user"""
    target_user = get_object_or_404(User, id=user_id)
    current_user = request.user
    
    # Business Head can only edit farmers and buyers
    if current_user.role == 'business_head':
        if target_user.role in ['admin', 'business_head']:
            messages.error(request, 'You can only edit farmers and buyers.')
            return redirect('user_list')
    
    if request.method == 'POST':
        form = UserEditForm(request.POST, instance=target_user)
        
        # Business Head cannot change user role to admin or business_head
        if current_user.role == 'business_head':
            new_role = request.POST.get('role')
            if new_role in ['admin', 'business_head']:
                messages.error(request, 'You cannot assign admin or business head roles.')
                return redirect('user_edit', user_id=user_id)
        
        if form.is_valid():
            form.save()
            
            # Log activity
            ActivityLog.objects.create(
                user=request.user,
                action='user_update',
                description=f'Updated user: {target_user.email}',
                ip_address=get_client_ip(request)
            )
            
            messages.success(request, f'User {target_user.email} updated successfully.')
            return redirect('user_list')
    else:
        form = UserEditForm(instance=target_user)
    
    # Restrict role choices for business_head
    if current_user.role == 'business_head':
        form.fields['role'].choices = [r for r in User.ROLE_CHOICES if r[0] in ['farmer', 'buyer']]
    
    return render(request, 'core/admin/user_form.html', {
        'form': form,
        'title': f'Edit User: {target_user.email}',
        'action': 'Update',
        'user_obj': target_user
    })


@login_required
@admin_or_business_head_required
def user_permissions(request, user_id):
    """Manage user permissions for categories with item-level control"""
    target_user = get_object_or_404(User, id=user_id)
    current_user = request.user
    
    # Business Head can only manage farmers and buyers, not admin or other business_heads
    if current_user.role == 'business_head':
        if target_user.role in ['admin', 'business_head']:
            messages.error(request, 'You can only manage permissions for farmers and buyers.')
            return redirect('user_list')
    
    categories = Category.objects.filter(is_active=True).prefetch_related(
        'subcategories__items'
    )
    
    if request.method == 'POST':
        # Clear existing permissions
        UserCategoryPermission.objects.filter(user=target_user).delete()
        target_user.allowed_categories.clear()
        
        # Add new permissions
        for category in categories:
            can_view = request.POST.get(f'can_view_{category.id}') == 'on'
            can_edit = request.POST.get(f'can_edit_{category.id}') == 'on'
            item_ids = request.POST.getlist(f'items_{category.id}')
            
            if can_view or can_edit:
                permission = UserCategoryPermission.objects.create(
                    user=target_user,
                    category=category,
                    can_view=can_view,
                    can_edit_price=can_edit
                )
                
                # Set item permissions
                if item_ids:
                    permission.items.set(Item.objects.filter(id__in=item_ids))
                    # Also set the subcategories for these items
                    subcategory_ids = Item.objects.filter(id__in=item_ids).values_list('subcategory_id', flat=True).distinct()
                    permission.subcategories.set(SubCategory.objects.filter(id__in=subcategory_ids))
                
                target_user.allowed_categories.add(category)
        
        # Log activity
        ActivityLog.objects.create(
            user=request.user,
            action='permission_change',
            description=f'Updated permissions for user: {target_user.email}',
            ip_address=get_client_ip(request)
        )
        
        messages.success(request, f'Permissions updated for {target_user.email}.')
        return redirect('user_list')
    
    # Get existing permissions
    existing_permissions = {}
    for perm in UserCategoryPermission.objects.filter(user=target_user).prefetch_related('subcategories', 'items'):
        existing_permissions[perm.category_id] = {
            'can_view': perm.can_view,
            'can_edit': perm.can_edit_price,
            'subcategories': list(perm.subcategories.values_list('id', flat=True)),
            'items': list(perm.items.values_list('id', flat=True))
        }
    
    context = {
        'user_obj': target_user,
        'categories': categories,
        'existing_permissions': existing_permissions,
    }
    return render(request, 'core/admin/user_permissions.html', context)


@login_required
@admin_or_business_head_required
def user_delete(request, user_id):
    """Delete a user"""
    target_user = get_object_or_404(User, id=user_id)
    current_user = request.user
    
    # Business Head can only delete farmers and buyers
    if current_user.role == 'business_head':
        if target_user.role in ['admin', 'business_head']:
            messages.error(request, 'You can only delete farmers and buyers.')
            return redirect('user_list')
    
    if request.method == 'POST':
        email = target_user.email
        target_user.delete()
        messages.success(request, f'User {email} deleted successfully.')
        return redirect('user_list')
    
    return render(request, 'core/admin/user_confirm_delete.html', {'user_obj': target_user})


@login_required
@admin_or_business_head_required
def category_list(request):
    """List all categories"""
    categories = Category.objects.all().prefetch_related('subcategories')
    return render(request, 'core/admin/category_list.html', {'categories': categories})


@login_required
@admin_or_business_head_required
def category_create(request):
    """Create a new category"""
    if request.method == 'POST':
        form = CategoryForm(request.POST, request.FILES)
        if form.is_valid():
            category = form.save()
            messages.success(request, f'Category {category.name} created successfully.')
            return redirect('category_list')
    else:
        form = CategoryForm()
    
    return render(request, 'core/admin/category_form.html', {
        'form': form,
        'title': 'Create Category',
        'action': 'Create'
    })


@login_required
@admin_or_business_head_required
def category_edit(request, category_id):
    """Edit a category"""
    category = get_object_or_404(Category, id=category_id)
    
    if request.method == 'POST':
        form = CategoryForm(request.POST, request.FILES, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, f'Category {category.name} updated successfully.')
            return redirect('category_list')
    else:
        form = CategoryForm(instance=category)
    
    return render(request, 'core/admin/category_form.html', {
        'form': form,
        'title': f'Edit Category: {category.name}',
        'action': 'Update',
        'category': category
    })


@login_required
@admin_or_business_head_required
def subcategory_create(request, category_id):
    """Create a new subcategory"""
    category = get_object_or_404(Category, id=category_id)
    
    if request.method == 'POST':
        form = SubCategoryForm(request.POST)
        if form.is_valid():
            subcategory = form.save()
            messages.success(request, f'Subcategory {subcategory.name} created successfully.')
            return redirect('category_list')
    else:
        form = SubCategoryForm(initial={'category': category})
    
    return render(request, 'core/admin/subcategory_form.html', {
        'form': form,
        'title': f'Add Subcategory to {category.name}',
        'action': 'Create',
        'category': category
    })


@login_required
@admin_or_business_head_required
def subcategory_edit(request, subcategory_id):
    """Edit a subcategory"""
    subcategory = get_object_or_404(SubCategory, id=subcategory_id)
    
    if request.method == 'POST':
        form = SubCategoryForm(request.POST, instance=subcategory)
        if form.is_valid():
            form.save()
            messages.success(request, f'Subcategory {subcategory.name} updated successfully.')
            return redirect('category_list')
    else:
        form = SubCategoryForm(instance=subcategory)
    
    return render(request, 'core/admin/subcategory_form.html', {
        'form': form,
        'title': f'Edit Subcategory: {subcategory.name}',
        'action': 'Update',
        'subcategory': subcategory
    })


@login_required
@admin_or_business_head_required
def region_list(request):
    """List all regions"""
    regions = Region.objects.all()
    return render(request, 'core/admin/region_list.html', {'regions': regions})


@login_required
@admin_or_business_head_required
def region_create(request):
    """Create a new region"""
    if request.method == 'POST':
        form = RegionForm(request.POST)
        if form.is_valid():
            region = form.save()
            messages.success(request, f'Region {region.name} created successfully.')
            return redirect('region_list')
    else:
        form = RegionForm()
    
    return render(request, 'core/admin/region_form.html', {
        'form': form,
        'title': 'Create Region',
        'action': 'Create'
    })


@login_required
@admin_or_business_head_required
def region_edit(request, region_id):
    """Edit a region"""
    region = get_object_or_404(Region, id=region_id)
    
    if request.method == 'POST':
        form = RegionForm(request.POST, instance=region)
        if form.is_valid():
            form.save()
            messages.success(request, f'Region {region.name} updated successfully.')
            return redirect('region_list')
    else:
        form = RegionForm(instance=region)
    
    return render(request, 'core/admin/region_form.html', {
        'form': form,
        'title': f'Edit Region: {region.name}',
        'action': 'Update',
        'region': region
    })


# ============ Farmer Management Views ============

@login_required
@admin_or_business_head_required
def farmer_list(request):
    """List all farmers"""
    farmers = Farmer.objects.all().select_related('region')
    return render(request, 'core/admin/farmer_list.html', {'farmers': farmers})


@login_required
@admin_or_business_head_required
def farmer_create(request):
    """Create a new farmer"""
    if request.method == 'POST':
        form = FarmerForm(request.POST)
        if form.is_valid():
            farmer = form.save()
            messages.success(request, f'Farmer {farmer.name} created successfully.')
            return redirect('farmer_list')
    else:
        form = FarmerForm()
    
    return render(request, 'core/admin/farmer_form.html', {
        'form': form,
        'title': 'Add Farmer',
        'action': 'Create'
    })


@login_required
@admin_or_business_head_required
def farmer_edit(request, farmer_id):
    """Edit a farmer"""
    farmer = get_object_or_404(Farmer, id=farmer_id)
    
    if request.method == 'POST':
        form = FarmerForm(request.POST, instance=farmer)
        if form.is_valid():
            form.save()
            messages.success(request, f'Farmer {farmer.name} updated successfully.')
            return redirect('farmer_list')
    else:
        form = FarmerForm(instance=farmer)
    
    return render(request, 'core/admin/farmer_form.html', {
        'form': form,
        'title': f'Edit Farmer: {farmer.name}',
        'action': 'Update',
        'farmer': farmer
    })


@login_required
@admin_or_business_head_required
def farmer_delete(request, farmer_id):
    """Delete a farmer"""
    farmer = get_object_or_404(Farmer, id=farmer_id)
    
    if request.method == 'POST':
        name = farmer.name
        farmer.delete()
        messages.success(request, f'Farmer {name} deleted successfully.')
        return redirect('farmer_list')
    
    return render(request, 'core/admin/farmer_confirm_delete.html', {
        'farmer': farmer
    })


@login_required
@admin_or_business_head_required
def farmer_assign_buyers(request, farmer_id):
    """Assign buyers to a farmer"""
    farmer = get_object_or_404(Farmer, id=farmer_id)
    
    # Get all buyers
    buyers = User.objects.filter(role='buyer', is_active=True).order_by('first_name', 'last_name')
    
    # Get currently assigned buyers
    assigned_buyer_ids = farmer.assigned_buyers.values_list('id', flat=True)
    
    if request.method == 'POST':
        # Get selected buyer IDs from form
        selected_buyer_ids = request.POST.getlist('buyers')
        
        # Update all buyers - remove this farmer from those not selected, add to those selected
        for buyer in buyers:
            if str(buyer.id) in selected_buyer_ids:
                buyer.assigned_farmers.add(farmer)
            else:
                buyer.assigned_farmers.remove(farmer)
        
        messages.success(request, f'Buyers assigned to {farmer.name} successfully.')
        return redirect('farmer_list')
    
    return render(request, 'core/admin/farmer_assign_buyers.html', {
        'farmer': farmer,
        'buyers': buyers,
        'assigned_buyer_ids': list(assigned_buyer_ids),
    })


# ============ API Views ============

@login_required
def api_get_subcategories(request, category_id):
    """API endpoint to get subcategories for a category"""
    subcategories = SubCategory.objects.filter(
        category_id=category_id, 
        is_active=True
    ).values('id', 'name', 'unit')
    return JsonResponse(list(subcategories), safe=False)


@login_required
def api_save_price(request):
    """API endpoint to save a single price entry (for auto-save)"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    user = request.user
    
    try:
        data = json.loads(request.body)
        item_id = data.get('item_id')
        farmer_id = data.get('farmer_id')
        price = data.get('price')
        date = data.get('date', timezone.now().date().isoformat())
        
        if not item_id:
            return JsonResponse({'error': 'Item ID is required'}, status=400)
        
        if isinstance(date, str):
            date = datetime.strptime(date, '%Y-%m-%d').date()
        
        # Get the item
        item = Item.objects.get(id=item_id, is_active=True)
        
        # Check permission
        category = item.subcategory.category
        if user.role not in ['admin']:
            permission = UserCategoryPermission.objects.filter(
                user=user, category=category, can_edit_price=True
            ).first()
            if not permission and not user.has_direct_access:
                return JsonResponse({'error': 'Permission denied'}, status=403)
        
        # Get the farmer if provided
        farmer = None
        if farmer_id:
            try:
                if user.role == 'admin':
                    farmer = Farmer.objects.get(id=farmer_id, is_active=True)
                else:
                    farmer = user.assigned_farmers.get(id=farmer_id, is_active=True)
            except Farmer.DoesNotExist:
                return JsonResponse({'error': 'Invalid farmer'}, status=400)
        
        # For buyers, farmer is required
        if user.role == 'buyer' and not farmer:
            return JsonResponse({'error': 'Farmer selection is required'}, status=400)
        
        # Handle empty price (delete the entry)
        if price is None or price == '' or price == 0:
            deleted, _ = PriceEntry.objects.filter(
                user=user,
                farmer=farmer,
                item=item,
                date=date
            ).delete()
            return JsonResponse({
                'success': True,
                'action': 'deleted' if deleted else 'no_change',
                'message': 'Price entry removed' if deleted else 'No price to remove'
            })
        
        # Save or update the price
        try:
            price = float(price)
        except (ValueError, TypeError):
            return JsonResponse({'error': 'Invalid price value'}, status=400)
        
        obj, created = PriceEntry.objects.update_or_create(
            user=user,
            farmer=farmer,
            item=item,
            date=date,
            defaults={'price': price, 'is_active': True}
        )
        
        # Log activity
        action = 'price_add' if created else 'price_update'
        farmer_info = f' from {farmer.name}' if farmer else ''
        ActivityLog.objects.create(
            user=user,
            action=action,
            description=f'Auto-saved price for {item.name}: ₹{price}{farmer_info}',
            ip_address=get_client_ip(request)
        )
        
        return JsonResponse({
            'success': True,
            'action': 'created' if created else 'updated',
            'entry_id': obj.id,
            'message': f'Price {"saved" if created else "updated"} successfully'
        })
    except Item.DoesNotExist:
        return JsonResponse({'error': 'Item not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


# ============ Helper Functions ============

def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


# ============ Approval & Notification APIs ============

@login_required
def api_toggle_price_approval(request):
    """API endpoint to toggle price approval status (Admin/Business Head only)"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    user = request.user
    
    # Only Admin and Business Head can approve prices
    if user.role not in ['admin', 'business_head']:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    try:
        data = json.loads(request.body)
        price_entry_id = data.get('price_entry_id')
        
        if not price_entry_id:
            return JsonResponse({'error': 'Price entry ID is required'}, status=400)
        
        price_entry = PriceEntry.objects.get(id=price_entry_id, is_active=True)
        
        # Toggle approval status
        if price_entry.is_approved:
            # Disapprove - remove approval and delete the notification
            price_entry.is_approved = False
            price_entry.approved_by = None
            price_entry.approved_at = None
            price_entry.save()
            
            # Delete the approval notification if it exists
            Notification.objects.filter(price_entry=price_entry, notification_type='price_approved').delete()
            
            return JsonResponse({
                'success': True,
                'is_approved': False,
                'message': 'Price disapproved'
            })
        else:
            # Approve
            price_entry.is_approved = True
            price_entry.approved_by = user
            price_entry.approved_at = timezone.now()
            price_entry.save()
            
            # Create notification for the user who entered the price
            item_name = price_entry.item.name if price_entry.item else 'Unknown'
            farmer_info = f' from {price_entry.farmer.name}' if price_entry.farmer else ''
            Notification.objects.create(
                user=price_entry.user,
                notification_type='price_approved',
                title='Price Approved',
                message=f'Your price of ₹{price_entry.price} for {item_name}{farmer_info} on {price_entry.date.strftime("%d %b, %Y")} was approved by {user.get_full_name()}.',
                price_entry=price_entry
            )
            
            return JsonResponse({
                'success': True,
                'is_approved': True,
                'approved_by': user.get_full_name(),
                'message': 'Price approved'
            })
    except PriceEntry.DoesNotExist:
        return JsonResponse({'error': 'Price entry not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
def api_get_notifications(request):
    """API endpoint to get user's notifications"""
    user = request.user
    
    # Get unread notifications (only approved ones - since we delete on disapprove)
    notifications = Notification.objects.filter(
        user=user,
        is_read=False
    ).select_related('price_entry', 'price_entry__item')[:20]
    
    notifications_data = []
    for notif in notifications:
        notifications_data.append({
            'id': notif.id,
            'type': notif.notification_type,
            'title': notif.title,
            'message': notif.message,
            'is_read': notif.is_read,
            'created_at': notif.created_at.strftime('%d %b, %Y %I:%M %p'),
            'time_ago': get_time_ago(notif.created_at)
        })
    
    # Get unread count
    unread_count = Notification.objects.filter(user=user, is_read=False).count()
    
    return JsonResponse({
        'success': True,
        'notifications': notifications_data,
        'unread_count': unread_count
    })


@login_required
def api_mark_notification_read(request):
    """API endpoint to mark notification(s) as read"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    user = request.user
    
    try:
        data = json.loads(request.body)
        notification_id = data.get('notification_id')
        mark_all = data.get('mark_all', False)
        
        if mark_all:
            # Mark all as read
            Notification.objects.filter(user=user, is_read=False).update(is_read=True)
            return JsonResponse({'success': True, 'message': 'All notifications marked as read'})
        elif notification_id:
            # Mark specific notification as read
            notification = Notification.objects.get(id=notification_id, user=user)
            notification.is_read = True
            notification.save()
            return JsonResponse({'success': True, 'message': 'Notification marked as read'})
        else:
            return JsonResponse({'error': 'notification_id or mark_all is required'}, status=400)
    except Notification.DoesNotExist:
        return JsonResponse({'error': 'Notification not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


def get_time_ago(dt):
    """Get human-readable time ago string"""
    now = timezone.now()
    diff = now - dt
    
    seconds = diff.total_seconds()
    if seconds < 60:
        return 'Just now'
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f'{minutes} min ago'
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f'{hours} hour{"s" if hours > 1 else ""} ago'
    elif seconds < 604800:
        days = int(seconds / 86400)
        return f'{days} day{"s" if days > 1 else ""} ago'
    else:
        return dt.strftime('%d %b, %Y')


# Store Manager Views
@admin_required
def create_store_manager_view(request):
    """Create a new store manager"""
    if request.method == 'POST':
        form = StoreManagerForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Log activity
            ActivityLog.objects.create(
                user=request.user,
                action='user_create',
                description=f'Created store manager: {user.get_full_name()} for {user.assigned_store.name}',
                ip_address=get_client_ip(request)
            )
            
            messages.success(request, f'Store manager {user.get_full_name()} created successfully!')
            return redirect('dashboard')
    else:
        form = StoreManagerForm()
    
    return render(request, 'core/user_form.html', {
        'form': form,
        'title': 'Create Store Manager'
    })


@admin_or_business_head_required
def create_team_leader_view(request):
    """Create a new team leader"""
    if request.method == 'POST':
        form = TeamLeaderForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Log activity
            ActivityLog.objects.create(
                user=request.user,
                action='user_create',
                description=f'Created team leader: {user.get_full_name()} for {user.assigned_store.name}',
                ip_address=get_client_ip(request)
            )
            
            messages.success(request, f'Team leader {user.get_full_name()} created successfully!')
            return redirect('dashboard')
    else:
        form = TeamLeaderForm()
    
    return render(request, 'core/user_form.html', {
        'form': form,
        'title': 'Create Team Leader'
    })


@admin_or_business_head_required
def create_store_head_view(request):
    """Create a new store head"""
    if request.method == 'POST':
        form = StoreHeadForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Get store names for logging
            store_names = ', '.join([store.name for store in user.managed_stores.all()])
            
            # Log activity
            ActivityLog.objects.create(
                user=request.user,
                action='user_create',
                description=f'Created store head: {user.get_full_name()} managing stores: {store_names}',
                ip_address=get_client_ip(request)
            )
            
            messages.success(request, f'Store head {user.get_full_name()} created successfully!')
            return redirect('dashboard')
    else:
        form = StoreHeadForm()
    
    return render(request, 'core/user_form.html', {
        'form': form,
        'title': 'Create Store Head'
    })


@login_required
def rating_form_view(request):
    """Rating form for store managers, team leaders, store heads, and admins"""
    # Check permissions
    if request.user.role not in ['store_manager', 'team_leader', 'store_head', 'admin', 'business_head']:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard')
    
    # For store heads and admins, check if they selected a store
    if request.user.role in ['store_head', 'admin', 'business_head']:
        store_id = request.session.get('selected_store_id')
        
        if request.user.role == 'store_head':
            # Store heads can only select from their managed stores
            if store_id:
                try:
                    store = request.user.managed_stores.get(id=store_id)
                except Store.DoesNotExist:
                    store = request.user.managed_stores.first()
                    if store:
                        request.session['selected_store_id'] = store.id
            else:
                store = request.user.managed_stores.first()
                if store:
                    request.session['selected_store_id'] = store.id
            managed_stores = request.user.managed_stores.filter(is_active=True)
        else:
            # Admins can select from all stores
            if store_id:
                try:
                    store = Store.objects.get(id=store_id, is_active=True)
                except Store.DoesNotExist:
                    store = Store.objects.filter(is_active=True).first()
                    if store:
                        request.session['selected_store_id'] = store.id
            else:
                store = Store.objects.filter(is_active=True).first()
                if store:
                    request.session['selected_store_id'] = store.id
            managed_stores = Store.objects.filter(is_active=True)
    else:
        # Store managers and team leaders use assigned store
        store = request.user.assigned_store
        if not store:
            messages.error(request, 'You are not assigned to any store.')
            return redirect('dashboard')
        managed_stores = None
    
    categories = Category.objects.filter(is_active=True)
    
    context = {
        'store': store,
        'managed_stores': managed_stores,
        'categories': categories,
    }
    
    return render(request, 'core/rating_form.html', context)


@login_required
def get_subcategories_api(request):
    """API to get subcategories for a category"""
    category_id = request.GET.get('category_id')
    
    if not category_id:
        return JsonResponse({'error': 'Category ID required'}, status=400)
    
    try:
        subcategories = SubCategory.objects.filter(
            category_id=category_id,
            is_active=True
        ).values('id', 'name').order_by('name')
        
        return JsonResponse({
            'success': True,
            'subcategories': list(subcategories)
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def get_items_api(request):
    """API to get items for a subcategory with existing ratings"""
    subcategory_id = request.GET.get('subcategory_id')
    
    # Get store_id based on user role
    if request.user.role in ['store_head', 'admin', 'business_head']:
        store_id = request.session.get('selected_store_id')
        if not store_id:
            if request.user.role == 'store_head':
                store_id = request.user.managed_stores.first().id if request.user.managed_stores.exists() else None
            else:
                store_id = Store.objects.filter(is_active=True).first().id if Store.objects.filter(is_active=True).exists() else None
    else:
        store_id = request.user.assigned_store.id if request.user.assigned_store else None
    
    today = timezone.now().date()
    
    if not subcategory_id:
        return JsonResponse({'success': False, 'error': 'Subcategory ID required'}, status=400)
    
    if not store_id:
        return JsonResponse({'success': False, 'error': 'No store selected'}, status=400)
    
    try:
        items = Item.objects.filter(
            subcategory_id=subcategory_id,
            is_active=True
        ).order_by('name')
        
        items_data = []
        for item in items:
            # Get today's rating for this user if exists
            rating = ItemRating.objects.filter(
                item=item,
                store_id=store_id,
                store_manager=request.user,
                rated_date=today
            ).first()
            
            items_data.append({
                'id': item.id,
                'name': item.name,
                'rating': rating.rating if rating else None,
                'comment': rating.comment if rating else ''
            })
        
        return JsonResponse({
            'success': True,
            'items': items_data
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def submit_ratings_api(request):
    """API to submit bulk ratings with photos"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)
    
    try:
        # Handle FormData instead of JSON
        ratings_json = request.POST.get('ratings')
        if not ratings_json:
            return JsonResponse({'error': 'No ratings provided'}, status=400)
            
        ratings_data = json.loads(ratings_json)
        
        # Get store based on user role
        if request.user.role in ['store_head', 'admin', 'business_head']:
            store_id = request.session.get('selected_store_id')
            if not store_id:
                return JsonResponse({'error': 'No store selected'}, status=400)
            try:
                if request.user.role == 'store_head':
                    store = request.user.managed_stores.get(id=store_id)
                else:
                    store = Store.objects.get(id=store_id, is_active=True)
            except Store.DoesNotExist:
                return JsonResponse({'error': 'Invalid store selected'}, status=400)
        else:
            store = request.user.assigned_store
            if not store:
                return JsonResponse({'error': 'No store assigned'}, status=400)
        
        today = timezone.now().date()
        
        created_count = 0
        updated_count = 0
        
        for rating_item in ratings_data:
            item_id = rating_item.get('item_id')
            rating_value = rating_item.get('rating')
            comment = rating_item.get('comment', '')
            has_photo = rating_item.get('has_photo', False)
            
            if item_id is None or rating_value is None:
                continue
            
            # Prepare defaults
            defaults = {
                'rating': rating_value,
                'comment': comment
            }
            
            # Add photo if provided
            if has_photo:
                photo_key = f'photo_{item_id}'
                if photo_key in request.FILES:
                    defaults['photo'] = request.FILES[photo_key]
            
            # Create or update rating for this user
            rating, created = ItemRating.objects.update_or_create(
                item_id=item_id,
                store=store,
                store_manager=request.user,
                rated_date=today,
                defaults=defaults
            )
            
            if created:
                created_count += 1
            else:
                updated_count += 1
        
        # Log activity
        ActivityLog.objects.create(
            user=request.user,
            action='rating_add' if created_count > 0 else 'rating_update',
            description=f'Submitted ratings for {created_count + updated_count} items at {store.name}',
            ip_address=get_client_ip(request)
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Successfully saved {created_count + updated_count} ratings',
            'created': created_count,
            'updated': updated_count
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def select_store_for_rating(request):
    """API for store heads and admins to select which store to rate"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)
    
    if request.user.role not in ['store_head', 'admin', 'business_head']:
        return JsonResponse({'error': 'Only store heads and admins can select stores'}, status=403)
    
    try:
        data = json.loads(request.body)
        store_id = data.get('store_id')
        
        if not store_id:
            return JsonResponse({'error': 'Store ID required'}, status=400)
        
        # Verify store access based on role
        if request.user.role == 'store_head':
            has_access = request.user.managed_stores.filter(id=store_id).exists()
        else:  # admin or business_head
            has_access = Store.objects.filter(id=store_id, is_active=True).exists()
        
        if has_access:
            request.session['selected_store_id'] = int(store_id)
            store = Store.objects.get(id=store_id)
            return JsonResponse({
                'success': True,
                'message': f'Now rating for {store.name}',
                'store_name': store.name
            })
        else:
            return JsonResponse({'error': 'You do not manage this store'}, status=403)
            
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Store.DoesNotExist:
        return JsonResponse({'error': 'Store not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@reports_access_required
def rating_reports_view(request):
    """Display rating reports for all stores (or managed stores for store heads)"""
    # Get filter parameters
    store_id = request.GET.get('store')
    category_id = request.GET.get('category')
    
    # Set default dates to today if not provided
    today = timezone.now().date().isoformat()
    date_from = request.GET.get('date_from', today)
    date_to = request.GET.get('date_to', today)
    
    rating_value = request.GET.get('rating')
    
    # Base queryset
    ratings = ItemRating.objects.select_related(
        'item', 'item__subcategory', 'item__subcategory__category', 
        'store', 'store_manager'
    ).all()
    
    # Filter by managed stores if user is a store head
    if request.user.role == 'store_head':
        ratings = ratings.filter(store__in=request.user.managed_stores.all())
    
    # Apply filters
    if store_id:
        ratings = ratings.filter(store_id=store_id)
    
    if category_id:
        ratings = ratings.filter(item__subcategory__category_id=category_id)
    
    if date_from:
        ratings = ratings.filter(rated_date__gte=date_from)
    
    if date_to:
        ratings = ratings.filter(rated_date__lte=date_to)
    
    if rating_value:
        ratings = ratings.filter(rating=rating_value)
    
    # Order by most recent
    ratings = ratings.order_by('-rated_date', '-id')
    
    # Get filter options
    stores = Store.objects.filter(is_active=True).order_by('name')
    # Filter stores for store heads
    if request.user.role == 'store_head':
        stores = stores.filter(id__in=request.user.managed_stores.values_list('id', flat=True))
    
    categories = Category.objects.filter(is_active=True).order_by('name')
    
    # Calculate summary statistics
    total_ratings = ratings.count()
    rating_na_count = ratings.filter(rating=-1).count()
    rating_0_count = ratings.filter(rating=0).count()
    rating_5_count = ratings.filter(rating=5).count()
    rating_10_count = ratings.filter(rating=10).count()
    
    # Average rating and percentages (exclude N/A from quality calculations)
    quality_ratings = ratings.exclude(rating=-1)
    total_quality_ratings = quality_ratings.count()
    avg_rating = 0
    rating_na_percent = 0
    rating_0_percent = 0
    rating_5_percent = 0
    rating_10_percent = 0
    
    if total_ratings > 0:
        rating_na_percent = round((rating_na_count * 100) / total_ratings, 1)
    
    if total_quality_ratings > 0:
        total_score = (rating_0_count * 0) + (rating_5_count * 5) + (rating_10_count * 10)
        avg_rating = round(total_score / total_quality_ratings, 2)
        rating_0_percent = round((rating_0_count * 100) / total_quality_ratings, 1)
        rating_5_percent = round((rating_5_count * 100) / total_quality_ratings, 1)
        rating_10_percent = round((rating_10_count * 100) / total_quality_ratings, 1)
    
    # Store-wise summary
    store_summary = {}
    for store in stores:
        store_ratings = ratings.filter(store=store)
        count = store_ratings.count()
        if count > 0:
            # Exclude N/A from quality average
            quality_store_ratings = store_ratings.exclude(rating=-1)
            quality_count = quality_store_ratings.count()
            if quality_count > 0:
                store_total = (quality_store_ratings.filter(rating=0).count() * 0 + 
                              quality_store_ratings.filter(rating=5).count() * 5 + 
                              quality_store_ratings.filter(rating=10).count() * 10)
                store_summary[store.id] = {
                    'store': store,
                    'count': count,
                    'avg': round(store_total / quality_count, 2)
                }
            else:
                store_summary[store.id] = {
                    'store': store,
                    'count': count,
                    'avg': 0
                }
    
    # Store Manager-wise summary - group by both manager and store
    from django.db.models import Count, Avg, Q
    manager_summary = ratings.values(
        'store_manager__id',
        'store_manager__first_name',
        'store_manager__last_name',
        'store_manager__username',
        'store_manager__role',
        'store_manager__assigned_store__name',
        'store__id',
        'store__name'
    ).annotate(
        total_ratings=Count('id'),
        rating_na_count=Count('id', filter=Q(rating=-1)),
        rating_0_count=Count('id', filter=Q(rating=0)),
        rating_5_count=Count('id', filter=Q(rating=5)),
        rating_10_count=Count('id', filter=Q(rating=10))
    ).order_by('-total_ratings')
    
    # Calculate average rating for each manager (excluding N/A)
    for manager in manager_summary:
        quality_count = manager['total_ratings'] - manager['rating_na_count']
        if quality_count > 0:
            total_score = (manager['rating_0_count'] * 0 + 
                          manager['rating_5_count'] * 5 + 
                          manager['rating_10_count'] * 10)
            manager['avg_rating'] = round(total_score / quality_count, 2)
        else:
            manager['avg_rating'] = 0
    
    context = {
        'ratings': ratings[:100],  # Limit to 100 for performance
        'total_ratings': total_ratings,
        'rating_na_count': rating_na_count,
        'rating_0_count': rating_0_count,
        'rating_5_count': rating_5_count,
        'rating_10_count': rating_10_count,
        'rating_na_percent': rating_na_percent,
        'rating_0_percent': rating_0_percent,
        'rating_5_percent': rating_5_percent,
        'rating_10_percent': rating_10_percent,
        'avg_rating': avg_rating,
        'store_summary': store_summary,
        'manager_summary': manager_summary,
        'stores': stores,
        'categories': categories,
        'selected_store': store_id,
        'selected_category': category_id,
        'date_from': date_from,
        'date_to': date_to,
        'selected_rating': rating_value,
    }
    
    return render(request, 'core/rating_reports.html', context)


@login_required
def ratings_list_view(request):
    """Display list of all ratings with role-based filtering"""
    # Check permissions
    if request.user.role not in ['store_head', 'admin', 'business_head']:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard')
    
    # Get filter parameters
    store_id = request.GET.get('store')
    category_id = request.GET.get('category')
    subcategory_id = request.GET.get('subcategory')
    
    # Set default dates to today if not provided
    today = timezone.now().date().isoformat()
    date_from = request.GET.get('date_from', today)
    date_to = request.GET.get('date_to', today)
    
    rating_value = request.GET.get('rating')
    manager_id = request.GET.get('manager')
    
    # Base queryset with relationships
    ratings = ItemRating.objects.select_related(
        'item', 
        'item__subcategory', 
        'item__subcategory__category', 
        'store', 
        'store_manager'
    ).all()
    
    # Role-based filtering
    if request.user.role == 'store_head':
        # Store heads see only their managed stores' ratings
        ratings = ratings.filter(store__in=request.user.managed_stores.all())
    
    # Apply filters
    if store_id:
        ratings = ratings.filter(store_id=store_id)
    
    if category_id:
        ratings = ratings.filter(item__subcategory__category_id=category_id)
    
    if subcategory_id:
        ratings = ratings.filter(item__subcategory_id=subcategory_id)
    
    if date_from:
        ratings = ratings.filter(rated_date__gte=date_from)
    
    if date_to:
        ratings = ratings.filter(rated_date__lte=date_to)
    
    if rating_value:
        ratings = ratings.filter(rating=rating_value)
    
    if manager_id:
        ratings = ratings.filter(store_manager_id=manager_id)
    
    # Order by most recent
    ratings = ratings.order_by('-rated_date', '-created_at')
    
    # Get filter options based on role
    stores = Store.objects.filter(is_active=True).order_by('name')
    if request.user.role == 'store_head':
        stores = stores.filter(id__in=request.user.managed_stores.values_list('id', flat=True))
    
    categories = Category.objects.filter(is_active=True).order_by('name')
    
    # Get store managers for filter
    managers = User.objects.filter(
        role__in=['store_manager', 'team_leader', 'store_head']
    ).order_by('first_name', 'last_name')
    if request.user.role == 'store_head':
        # Only show managers from their stores
        managers = managers.filter(
            Q(assigned_store__in=request.user.managed_stores.all()) |
            Q(managed_stores__in=request.user.managed_stores.all())
        ).distinct()
    
    # Calculate summary statistics (before pagination)
    total_ratings = ratings.count()
    rating_na_count = ratings.filter(rating=-1).count()
    rating_0_count = ratings.filter(rating=0).count()
    rating_5_count = ratings.filter(rating=5).count()
    rating_10_count = ratings.filter(rating=10).count()
    
    # Average rating (exclude N/A from quality calculations)
    quality_ratings = ratings.exclude(rating=-1)
    total_quality_ratings = quality_ratings.count()
    avg_rating = 0
    if total_quality_ratings > 0:
        total_score = (rating_0_count * 0) + (rating_5_count * 5) + (rating_10_count * 10)
        avg_rating = round(total_score / total_quality_ratings, 2)
    
    # Pagination
    from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
    
    paginator = Paginator(ratings, 200)  # 200 items per page
    page = request.GET.get('page', 1)
    
    try:
        ratings_page = paginator.page(page)
    except PageNotAnInteger:
        ratings_page = paginator.page(1)
    except EmptyPage:
        ratings_page = paginator.page(paginator.num_pages)
    
    context = {
        'ratings': ratings_page,
        'stores': stores,
        'categories': categories,
        'managers': managers,
        'total_ratings': total_ratings,
        'rating_na_count': rating_na_count,
        'rating_0_count': rating_0_count,
        'rating_5_count': rating_5_count,
        'rating_10_count': rating_10_count,
        'avg_rating': avg_rating,
        'selected_store': store_id,
        'selected_category': category_id,
        'selected_subcategory': subcategory_id,
        'date_from': date_from,
        'date_to': date_to,
        'selected_rating': rating_value,
        'selected_manager': manager_id,
    }
    
    return render(request, 'core/ratings_list.html', context)
