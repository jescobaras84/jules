from django.urls import path
from . import views

app_name = 'invoicing'
urlpatterns = [
    path('', views.home_view, name='home'), # A simple home view
    path('restricted_page/', views.restricted_view, name='restricted_page'),
    # Add other app-specific URLs here
]
urlpatterns += [
    path('products/', views.product_list_view, name='product_list'),
    path('products/new/', views.product_create_view, name='product_create'),
    path('products/<int:pk>/edit/', views.product_update_view, name='product_update'),
    path('products/<int:pk>/', views.product_detail_view, name='product_detail'),
]
urlpatterns += [
    path('products/add_stock/', views.product_add_stock_view, name='product_add_stock'),
    path('products/<int:pk>/add_stock/', views.product_add_stock_view, name='product_add_stock_specific'),
]
urlpatterns += [
    path('invoices/', views.invoice_list_view, name='invoice_list'),
    path('invoices/new/', views.invoice_create_view, name='invoice_create'),
    path('invoices/<int:pk>/', views.invoice_detail_view, name='invoice_detail'),
]
urlpatterns += [
    path('purchase_orders/', views.purchase_order_list_view, name='po_list'),
    path('purchase_orders/new/', views.purchase_order_create_view, name='po_create'),
    path('purchase_orders/<int:pk>/', views.purchase_order_detail_view, name='po_detail'),
    path('purchase_orders/<int:pk>/fulfill/', views.purchase_order_fulfill_view, name='po_fulfill'),
]

# Customer URLs
urlpatterns += [
    path('customers/', views.customer_list_view, name='customer_list'),
    path('customers/new/', views.customer_create_view, name='customer_create'),
    path('customers/<int:pk>/', views.customer_detail_view, name='customer_detail'),
    path('customers/<int:pk>/edit/', views.customer_update_view, name='customer_update'),
]

# Supplier URLs
urlpatterns += [
    path('suppliers/', views.supplier_list_view, name='supplier_list'),
    path('suppliers/new/', views.supplier_create_view, name='supplier_create'),
    path('suppliers/<int:pk>/', views.supplier_detail_view, name='supplier_detail'),
    path('suppliers/<int:pk>/edit/', views.supplier_update_view, name='supplier_update'),
]

# AJAX URLs
urlpatterns += [
    path('ajax/add_customer/', views.ajax_add_customer, name='ajax_add_customer'),
]
