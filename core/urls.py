from django.urls import path
from . import views

urlpatterns = [
    # Authentication
    path('', views.login_view, name='login'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Categories
    path('category/<int:category_id>/', views.category_detail, name='category_detail'),
    path('category/<int:category_id>/subcategory/<int:subcategory_id>/', views.subcategory_detail, name='subcategory_detail'),
    path('category/<int:category_id>/enter-price/', views.enter_price, name='enter_price'),
    path('category/<int:category_id>/subcategory/<int:subcategory_id>/enter-price/', views.enter_price, name='enter_price_subcategory'),
    path('category/<int:category_id>/price-history/', views.category_price_history, name='category_price_history'),
    
    # Admin URLs
    path('admin-panel/', views.admin_dashboard, name='admin_dashboard'),
    
    # User Management
    path('admin-panel/users/', views.user_list, name='user_list'),
    path('admin-panel/users/create/', views.user_create, name='user_create'),
    path('admin-panel/users/<int:user_id>/edit/', views.user_edit, name='user_edit'),
    path('admin-panel/users/<int:user_id>/permissions/', views.user_permissions, name='user_permissions'),
    path('admin-panel/users/<int:user_id>/delete/', views.user_delete, name='user_delete'),
    
    # Category Management
    path('admin-panel/categories/', views.category_list, name='category_list'),
    path('admin-panel/categories/create/', views.category_create, name='category_create'),
    path('admin-panel/categories/<int:category_id>/edit/', views.category_edit, name='category_edit'),
    path('admin-panel/categories/<int:category_id>/subcategory/create/', views.subcategory_create, name='subcategory_create'),
    path('admin-panel/subcategories/<int:subcategory_id>/edit/', views.subcategory_edit, name='subcategory_edit'),
    
    # Region Management
    path('admin-panel/regions/', views.region_list, name='region_list'),
    path('admin-panel/regions/create/', views.region_create, name='region_create'),
    path('admin-panel/regions/<int:region_id>/edit/', views.region_edit, name='region_edit'),
    
    # Farmer Management
    path('admin-panel/farmers/', views.farmer_list, name='farmer_list'),
    path('admin-panel/farmers/create/', views.farmer_create, name='farmer_create'),
    path('admin-panel/farmers/<int:farmer_id>/edit/', views.farmer_edit, name='farmer_edit'),
    path('admin-panel/farmers/<int:farmer_id>/delete/', views.farmer_delete, name='farmer_delete'),
    path('admin-panel/farmers/<int:farmer_id>/assign-buyers/', views.farmer_assign_buyers, name='farmer_assign_buyers'),

    # API endpoints
    path('api/subcategories/<int:category_id>/', views.api_get_subcategories, name='api_get_subcategories'),
    path('api/save-price/', views.api_save_price, name='api_save_price'),
    path('api/toggle-price-approval/', views.api_toggle_price_approval, name='api_toggle_price_approval'),
    path('api/notifications/', views.api_get_notifications, name='api_get_notifications'),
    path('api/notifications/mark-read/', views.api_mark_notification_read, name='api_mark_notification_read'),

    # Store Manager URLs
    path('create-store-manager/', views.create_store_manager_view, name='create_store_manager'),
    path('create-team-leader/', views.create_team_leader_view, name='create_team_leader'),
    path('create-store-head/', views.create_store_head_view, name='create_store_head'),
    path('rate-items/', views.rating_form_view, name='rating_form'),
    path('ratings-list/', views.ratings_list_view, name='ratings_list'),
    path('rating-reports/', views.rating_reports_view, name='rating_reports'),
    path('api/rating/subcategories/', views.get_subcategories_api, name='api_rating_subcategories'),
    path('api/rating/items/', views.get_items_api, name='api_rating_items'),
    path('api/rating/submit/', views.submit_ratings_api, name='api_submit_ratings'),
    path('api/rating/select-store/', views.select_store_for_rating, name='api_select_store'),

]
