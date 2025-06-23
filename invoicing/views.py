# invoicing/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import Group
from django.http import HttpResponse, JsonResponse # Asegúrate que JsonResponse esté aquí
from django.contrib import messages
from django.db import transaction, models # 'models' es para models.ProtectedError
from decimal import Decimal
from django.utils.translation import gettext_lazy as _ # Para traducción

# Modelos de tu aplicación
from .models import (
    Product, Invoice, InvoiceItem, PurchaseOrder, PurchaseOrderItem,
    Customer, Supplier, Role # Customer, Supplier y Role son importantes aquí
)

# Formularios de tu aplicación
from .forms import (
    ProductForm, AddStockForm,
    InvoiceForm, InvoiceItemFormSet,
    PurchaseOrderForm, PurchaseOrderItemFormSet,
    CustomerForm, SupplierForm, CustomerQuickAddForm, SupplierQuickAddForm # Formularios de Customer y Supplier
)

# Conversion factors (asegúrate que esté definido globalmente o antes de las vistas que lo usan)
CONVERSION_FACTORS_ML = {
    'ml': Decimal('1.0'),
    'litre': Decimal('1000.0'),
    'gallon': Decimal('3785.41'),
    'pichinga': Decimal('18927.1'), # Asegúrate que esta línea esté presente
}

# Decorator for role-based access (asegúrate que esté definido)
def group_required(*group_names):
    """Requires user membership in at least one of the groups passed in."""
    def in_groups(u):
        if u.is_authenticated:
            if bool(u.groups.filter(name__in=group_names)) | u.is_superuser:
                return True
        return False
    return user_passes_test(in_groups, login_url='login')
@login_required
def home_view(request):
    return render(request, 'invoicing/home.html')

@login_required
@group_required('Admin') # Example: Only users in 'Admin' group can access
def restricted_view(request):
    return HttpResponse("Welcome to the restricted Admin page!")

# Django's built-in views (LoginView, LogoutView) will be used via django.contrib.auth.urls
# We just need to provide the templates.
@login_required
# @group_required('Admin', 'InventoryManager') # Add 'InventoryManager' if that group is planned
def product_list_view(request):
    products = Product.objects.all().order_by('name')
    return render(request, 'invoicing/product_list.html', {'products': products})

@login_required
@group_required('Admin')
def product_create_view(request):
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            form.save()
            # messages.success(request, 'Product created successfully!') # Optional: Add user messages
            return redirect('invoicing:product_list')
    else:
        form = ProductForm()
    return render(request, 'invoicing/product_form.html', {'form': form, 'title': 'Create New Product'})

@login_required
@group_required('Admin')
def product_update_view(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            # messages.success(request, 'Product updated successfully!')
            return redirect('invoicing:product_list')
    else:
        form = ProductForm(instance=product)
    return render(request, 'invoicing/product_form.html', {'form': form, 'title': f'Edit {product.name}'})

@login_required
# @group_required('Admin', 'InventoryManager', 'Salesperson') # Salesperson might need to view details
def product_detail_view(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, 'invoicing/product_detail.html', {'product': product})

@login_required
@group_required('Admin', 'InventoryManager') # Or appropriate group
def product_add_stock_view(request, pk=None): # pk is optional for pre-selecting product
    initial_data = {}
    if pk:
        product = get_object_or_404(Product, pk=pk)
        initial_data['product'] = product

    if request.method == 'POST':
        form = AddStockForm(request.POST)
        if form.is_valid():
            product_to_update = form.cleaned_data['product']
            quantity_added = form.cleaned_data['quantity_ml_added']

            product_to_update.current_stock_ml += quantity_added
            product_to_update.save()

            messages.success(request, f"Successfully added {quantity_added} ml to {product_to_update.name}. New stock: {product_to_update.current_stock_ml} ml.")
            return redirect('invoicing:product_detail', pk=product_to_update.pk)
    else:
        form = AddStockForm(initial=initial_data)

    return render(request, 'invoicing/product_add_stock.html', {'form': form, 'title': 'Add Stock to Product'})

# Placeholder for stock deduction logic (to be used by Invoicing)
def deduct_stock(product_id, quantity_ml_to_deduct):
    try:
        product = Product.objects.get(pk=product_id)
        if product.current_stock_ml >= quantity_ml_to_deduct:
            product.current_stock_ml -= quantity_ml_to_deduct
            product.save()
            # Check for low stock after deduction
            if product.current_stock_ml < product.minimum_stock_ml:
                # This is a place where a more robust notification system could be triggered
                print(f"Warning: Product {product.name} is below minimum stock level!")
            return True, "Stock deducted successfully."
        else:
            return False, f"Not enough stock for {product.name}. Available: {product.current_stock_ml} ml, Tried to deduct: {quantity_ml_to_deduct} ml."
    except Product.DoesNotExist:
        return False, "Product not found."

# Conversion factors
CONVERSION_FACTORS_ML = {
    'ml': Decimal('1.0'),
    'litre': Decimal('1000.0'),
    'gallon': Decimal('3785.41'),
}

@login_required
@group_required('Admin', 'Salesperson')
@transaction.atomic # Ensure all operations are successful or none are
def invoice_create_view(request):
    if request.method == 'POST':
        invoice_form = InvoiceForm(request.POST)
        item_formset = InvoiceItemFormSet(request.POST, prefix='items')

        if invoice_form.is_valid() and item_formset.is_valid():
            invoice = invoice_form.save(commit=False)
            # invoice.user = request.user # Assign user if field exists
            invoice.total_amount = Decimal('0.00') # Initialize total amount
            invoice.save() # Save invoice first to get an ID for items

            items_to_save = []
            total_invoice_amount = Decimal('0.00')

            for form in item_formset:
                if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                    item = form.save(commit=False)
                    item.invoice = invoice

                    product = form.cleaned_data['product']
                    quantity_input = form.cleaned_data['quantity_input']
                    unit_of_measure = form.cleaned_data['unit_of_measure']
                    unit_price_input = form.cleaned_data['unit_price'] # Price for the unit sold

                    # Calculate quantity in ml for inventory
                    item.quantity_ml = quantity_input * CONVERSION_FACTORS_ML[unit_of_measure]
                    item.unit_price = unit_price_input # Store the unit price as it was entered (e.g. price per gallon)

                    # Calculate line total
                    item.line_total = quantity_input * unit_price_input # Total for this line item
                    total_invoice_amount += item.line_total

                    # Deduct stock
                    success, message = deduct_stock(product.id, item.quantity_ml)
                    if not success:
                        messages.error(request, f"Error for product {product.name}: {message}")
                        # This is a simplified error handling. Ideally, add errors to specific forms.
                        # For now, re-rendering with a general error.
                        return render(request, 'invoicing/invoice_create.html', {
                            'invoice_form': invoice_form,
                            'item_formset': item_formset,
                            'title': 'Create Sales Invoice'
                        })

                    items_to_save.append(item)

            if items_to_save:
                InvoiceItem.objects.bulk_create(items_to_save)
                invoice.total_amount = total_invoice_amount
                invoice.save()
                messages.success(request, 'Invoice created successfully!')
                return redirect('invoicing:invoice_detail', pk=invoice.pk)
            else:
                messages.warning(request, "No items were added to the invoice. Invoice not created.")
                invoice.delete()
                return redirect('invoicing:invoice_create')

        else:
            messages.error(request, "Please correct the errors below.")
    else:
        invoice_form = InvoiceForm()
        item_formset = InvoiceItemFormSet(prefix='items', queryset=InvoiceItem.objects.none())

    return render(request, 'invoicing/invoice_create.html', {
        'invoice_form': invoice_form,
        'item_formset': item_formset,
        'title': 'Create Sales Invoice'
    })

@login_required
def invoice_list_view(request):
    invoices = Invoice.objects.all().order_by('-invoice_date')
    return render(request, 'invoicing/invoice_list.html', {'invoices': invoices})

@login_required
def invoice_detail_view(request, pk):
    invoice = get_object_or_404(Invoice.objects.prefetch_related('items', 'items__product'), pk=pk)
    return render(request, 'invoicing/invoice_detail.html', {'invoice': invoice})

@login_required
@group_required('Admin', 'InventoryManager')
@transaction.atomic
def purchase_order_create_view(request):
    if request.method == 'POST':
        po_form = PurchaseOrderForm(request.POST)
        item_formset = PurchaseOrderItemFormSet(request.POST, prefix='items')

        if po_form.is_valid() and item_formset.is_valid():
            purchase_order = po_form.save(commit=False)
            # purchase_order.user = request.user # If user is linked
            purchase_order.total_cost = Decimal('0.00') # Initialize
            purchase_order.save() # Save PO first

            items_to_save = []
            total_po_cost = Decimal('0.00')

            for form in item_formset:
                if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                    item = form.save(commit=False)
                    item.purchase_order = purchase_order

                    # Calculate line total (already done by model's save if not here)
                    item.line_total = item.quantity_ml * item.unit_cost
                    total_po_cost += item.line_total
                    items_to_save.append(item)

            if items_to_save:
                PurchaseOrderItem.objects.bulk_create(items_to_save)
                purchase_order.total_cost = total_po_cost
                purchase_order.save()
                messages.success(request, 'Purchase Order created successfully.')
                return redirect('invoicing:po_detail', pk=purchase_order.pk)
            else:
                messages.warning(request, "No items added to Purchase Order. PO not created.")
                purchase_order.delete()
                return redirect('invoicing:po_create')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        po_form = PurchaseOrderForm()
        item_formset = PurchaseOrderItemFormSet(prefix='items', queryset=PurchaseOrderItem.objects.none())

    return render(request, 'invoicing/po_create.html', {
        'po_form': po_form,
        'item_formset': item_formset,
        'title': 'Create Purchase Order'
    })

@login_required
def purchase_order_list_view(request):
    purchase_orders = PurchaseOrder.objects.all().order_by('-order_date')
    return render(request, 'invoicing/po_list.html', {'purchase_orders': purchase_orders})

@login_required
def purchase_order_detail_view(request, pk):
    purchase_order = get_object_or_404(PurchaseOrder.objects.prefetch_related('items', 'items__product'), pk=pk)
    return render(request, 'invoicing/po_detail.html', {'purchase_order': purchase_order})

@login_required
@group_required('Admin', 'InventoryManager')
@transaction.atomic
def purchase_order_fulfill_view(request, pk):
    purchase_order = get_object_or_404(PurchaseOrder.objects.prefetch_related('items__product'), pk=pk)
    if purchase_order.is_fulfilled:
        messages.warning(request, f"Purchase Order {purchase_order.id} has already been fulfilled.")
        return redirect('invoicing:po_detail', pk=purchase_order.pk)

    if request.method == 'POST': # Confirmation step
        for item in purchase_order.items.all():
            product = item.product
            product.current_stock_ml += item.quantity_ml
            product.save()
            # Log this stock addition if necessary (e.g., in a separate StockMovement model)

        purchase_order.is_fulfilled = True
        purchase_order.save()
        messages.success(request, f"Purchase Order {purchase_order.id} marked as fulfilled and stock updated.")
        return redirect('invoicing:po_detail', pk=purchase_order.pk)

    # If GET, could show a confirmation page, but for simplicity, POST directly fulfills.
    # Or, redirect back if GET request not meant for direct action.
    # For this iteration, we'll make GET redirect with an error, as POST is expected.
    messages.error(request, "Invalid request method for fulfilling PO. Please use the button on the PO detail page.")
    return redirect('invoicing:po_detail', pk=purchase_order.pk)
