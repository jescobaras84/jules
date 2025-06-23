
from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import Group
from django.db import transaction, models
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.translation import gettext_lazy as _

from .models import (
    Product, Invoice, InvoiceItem, PurchaseOrder, PurchaseOrderItem,
    Customer, Supplier, Role
)

from .forms import (
    ProductForm, AddStockForm,
    InvoiceForm, InvoiceItemFormSet,
    PurchaseOrderForm, PurchaseOrderItemFormSet,
    CustomerForm, SupplierForm, CustomerQuickAddForm, SupplierQuickAddForm
)

CONVERSION_FACTORS_ML = {
    'ml': Decimal('1.0'),
    'litre': Decimal('1000.0'),
    'gallon': Decimal('3785.41'),
    'pichinga': Decimal('18927.1'),
}

def group_required(*group_names):
    def in_groups(u):
        if u.is_authenticated:
            return u.groups.filter(name__in=group_names).exists() or u.is_superuser
        return False
    return user_passes_test(in_groups, login_url='login')

@login_required
def home_view(request):
    return render(request, 'invoicing/home.html')

@login_required
@group_required('Admin')
def restricted_view(request):
    return HttpResponse("Welcome to the restricted Admin page!")

@login_required
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
            return redirect('invoicing:product_list')
    else:
        form = ProductForm(instance=product)
    return render(request, 'invoicing/product_form.html', {'form': form, 'title': f'Edit {product.name}'})

@login_required
def product_detail_view(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, 'invoicing/product_detail.html', {'product': product})

@login_required
@group_required('Admin', 'InventoryManager')
def product_add_stock_view(request, pk=None):
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
            messages.success(request, f"{quantity_added} ml added to {product_to_update.name}.")
            return redirect('invoicing:product_detail', pk=product_to_update.pk)
    else:
        form = AddStockForm(initial=initial_data)

    return render(request, 'invoicing/product_add_stock.html', {'form': form, 'title': 'Add Stock'})

def deduct_stock(product_id, quantity_ml_to_deduct):
    try:
        product = Product.objects.get(pk=product_id)
        if product.current_stock_ml >= quantity_ml_to_deduct:
            product.current_stock_ml -= quantity_ml_to_deduct
            product.save()
            if product.current_stock_ml < product.minimum_stock_ml:
                print(f"Warning: {product.name} is below minimum stock level.")
            return True, "Stock deducted."
        return False, f"Insufficient stock for {product.name}."
    except Product.DoesNotExist:
        return False, "Product not found."

# === Customer CRUD Views ===---*-*-*-*-
@login_required
def customer_list_view(request):
    customers = Customer.objects.all().order_by('name')
    return render(request, 'invoicing/customer_list.html', {'customers': customers, 'title': _('Customers')})

@login_required
def customer_detail_view(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    # Pasamos 'object' para consistencia con la plantilla de confirmación de borrado
    # y 'customer' para acceso directo en la plantilla de detalle.
    return render(request, 'invoicing/customer_detail.html', {'object': customer, 'customer': customer, 'title': customer.name})

@login_required
@group_required('Admin', 'Salesperson') # Ajusta los permisos de grupo según necesites
def customer_create_view(request):
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            customer = form.save()
            messages.success(request, _('Customer "%(name)s" created successfully.') % {'name': customer.name})
            return redirect('invoicing:customer_list')
    else:
        form = CustomerForm()
    return render(request, 'invoicing/customer_form.html', {'form': form, 'title': _('Create New Customer')})

@login_required
@group_required('Admin', 'Salesperson') # Ajusta los permisos de grupo según necesites
def customer_update_view(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == 'POST':
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            messages.success(request, _('Customer "%(name)s" updated successfully.') % {'name': customer.name})
            return redirect('invoicing:customer_detail', pk=customer.pk)
    else:
        form = CustomerForm(instance=customer)
    # Pasamos 'object' para la plantilla de formulario por si se reusa con 'delete'
    return render(request, 'invoicing/customer_form.html', {'form': form, 'object': customer, 'title': _('Edit %s') % customer.name})

@login_required
@group_required('Admin') # Eliminar suele ser una acción más restringida
def customer_delete_view(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == 'POST': # Confirmación de borrado
        try:
            customer_name = customer.name # Guardar nombre para el mensaje
            customer.delete()
            messages.success(request, _('Customer "%(name)s" deleted successfully.') % {'name': customer_name})
            return redirect('invoicing:customer_list')
        except models.ProtectedError as e:
            messages.error(request, _("Cannot delete customer '%(name)s' as it is linked to other records. Details: %(error)s") % {'name': customer.name, 'error': e})
            return redirect('invoicing:customer_detail', pk=pk)
        except Exception as e:
            messages.error(request, _("An unexpected error occurred while trying to delete customer '%(name)s'. Error: %(error)s") % {'name': customer.name, 'error': e})
            return redirect('invoicing:customer_detail', pk=pk)
    # Para peticiones GET, se muestra la plantilla de confirmación
    return render(request, 'invoicing/customer_confirm_delete.html', {'object': customer, 'title': _('Delete Customer: %s') % customer.name})

# === Supplier CRUD Views ===
@login_required
def supplier_list_view(request):
    suppliers = Supplier.objects.all().order_by('name')
    return render(request, 'invoicing/supplier_list.html', {'suppliers': suppliers, 'title': _('Suppliers')})

@login_required
def supplier_detail_view(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    # Pasamos 'object' para consistencia con la plantilla de confirmación de borrado
    # y 'supplier' para acceso directo en la plantilla de detalle (aunque 'object' sería suficiente).
    return render(request, 'invoicing/supplier_detail.html', {'object': supplier, 'supplier': supplier, 'title': supplier.name})

@login_required
@group_required('Admin', 'InventoryManager') # Ajusta los permisos de grupo según necesites
def supplier_create_view(request):
    if request.method == 'POST':
        form = SupplierForm(request.POST)
        if form.is_valid():
            supplier = form.save()
            messages.success(request, _('Supplier "%(name)s" created successfully.') % {'name': supplier.name})
            return redirect('invoicing:supplier_list')
    else:
        form = SupplierForm()
    return render(request, 'invoicing/supplier_form.html', {'form': form, 'title': _('Create New Supplier')})

@login_required
@group_required('Admin', 'InventoryManager') # Ajusta los permisos de grupo según necesites
def supplier_update_view(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    if request.method == 'POST':
        form = SupplierForm(request.POST, instance=supplier)
        if form.is_valid():
            form.save()
            messages.success(request, _('Supplier "%(name)s" updated successfully.') % {'name': supplier.name})
            return redirect('invoicing:supplier_detail', pk=supplier.pk)
    else:
        form = SupplierForm(instance=supplier)
    return render(request, 'invoicing/supplier_form.html', {'form': form, 'object': supplier, 'title': _('Edit %s') % supplier.name})

@login_required
@group_required('Admin') # Eliminar suele ser una acción más restringida
def supplier_delete_view(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    if request.method == 'POST': # Confirmación de borrado
        try:
            supplier_name = supplier.name # Guardar nombre para el mensaje
            supplier.delete()
            messages.success(request, _('Supplier "%(name)s" deleted successfully.') % {'name': supplier_name})
            return redirect('invoicing:supplier_list')
        except models.ProtectedError as e:
            messages.error(request, _("Cannot delete supplier '%(name)s' as it is linked to other records. Details: %(error)s") % {'name': supplier.name, 'error': e})
            return redirect('invoicing:supplier_detail', pk=pk)
        except Exception as e:
            messages.error(request, _("An unexpected error occurred while trying to delete supplier '%(name)s'. Error: %(error)s") % {'name': supplier.name, 'error': e})
            return redirect('invoicing:supplier_detail', pk=pk)
    # Para peticiones GET, se muestra la plantilla de confirmación
    return render(request, 'invoicing/supplier_confirm_delete.html', {'object': supplier, 'title': _('Delete Supplier: %s') % supplier.name})

# === AJAX Views for Quick Add ===
@login_required
def ajax_add_customer(request):
    if request.method == 'POST':
        form = CustomerQuickAddForm(request.POST)
        if form.is_valid():
            customer = form.save()
            return JsonResponse({'status': 'success', 'customer_id': customer.pk, 'customer_name': customer.name})
        else:
            # Collect form errors into a serializable format
            errors = {field: [e for e in error_list] for field, error_list in form.errors.items()}
            return JsonResponse({'status': 'error', 'errors': errors}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=405)

@login_required
def ajax_add_supplier(request):
    if request.method == 'POST':
        form = SupplierQuickAddForm(request.POST)
        if form.is_valid():
            supplier = form.save()
            return JsonResponse({'status': 'success', 'supplier_id': supplier.pk, 'supplier_name': supplier.name})
        else:
            errors = {field: [e for e in error_list] for field, error_list in form.errors.items()}
            return JsonResponse({'status': 'error', 'errors': errors}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=405)

# === Customer CRUD Views ===
@login_required
def customer_list_view(request):
    customers = Customer.objects.all().order_by('name')
    return render(request, 'invoicing/customer_list.html', {'customers': customers, 'title': _('Customers')})

@login_required
def customer_detail_view(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    # Pasamos 'object' para consistencia con la plantilla de confirmación de borrado
    # y 'customer' para acceso directo en la plantilla de detalle.
    return render(request, 'invoicing/customer_detail.html', {'object': customer, 'customer': customer, 'title': customer.name})

@login_required
@group_required('Admin', 'Salesperson') # Ajusta los permisos de grupo según necesites
def customer_create_view(request):
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            customer = form.save()
            messages.success(request, _('Customer "%(name)s" created successfully.') % {'name': customer.name})
            return redirect('invoicing:customer_list')
    else:
        form = CustomerForm()
    return render(request, 'invoicing/customer_form.html', {'form': form, 'title': _('Create New Customer')})

@login_required
@group_required('Admin', 'Salesperson') # Ajusta los permisos de grupo según necesites
def customer_update_view(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == 'POST':
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            messages.success(request, _('Customer "%(name)s" updated successfully.') % {'name': customer.name})
            return redirect('invoicing:customer_detail', pk=customer.pk)
    else:
        form = CustomerForm(instance=customer)
    # Pasamos 'object' para la plantilla de formulario por si se reusa con 'delete'
    return render(request, 'invoicing/customer_form.html', {'form': form, 'object': customer, 'title': _('Edit %s') % customer.name})

@login_required
@group_required('Admin') # Eliminar suele ser una acción más restringida
def customer_delete_view(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == 'POST': # Confirmación de borrado
        try:
            customer_name = customer.name # Guardar nombre para el mensaje
            customer.delete()
            messages.success(request, _('Customer "%(name)s" deleted successfully.') % {'name': customer_name})
            return redirect('invoicing:customer_list')
        except models.ProtectedError as e:
            messages.error(request, _("Cannot delete customer '%(name)s' as it is linked to other records. Details: %(error)s") % {'name': customer.name, 'error': e})
            return redirect('invoicing:customer_detail', pk=pk)
        except Exception as e:
            messages.error(request, _("An unexpected error occurred while trying to delete customer '%(name)s'. Error: %(error)s") % {'name': customer.name, 'error': e})
            return redirect('invoicing:customer_detail', pk=pk)
    # Para peticiones GET, se muestra la plantilla de confirmación
    return render(request, 'invoicing/customer_confirm_delete.html', {'object': customer, 'title': _('Delete Customer: %s') % customer.name})

# === Supplier CRUD Views ===
@login_required
def supplier_list_view(request):
    suppliers = Supplier.objects.all().order_by('name')
    return render(request, 'invoicing/supplier_list.html', {'suppliers': suppliers, 'title': _('Suppliers')})

@login_required
def supplier_detail_view(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    # Pasamos 'object' para consistencia con la plantilla de confirmación de borrado
    return render(request, 'invoicing/supplier_detail.html', {'object': supplier, 'title': supplier.name})

@login_required
@group_required('Admin', 'InventoryManager') # Ajusta los permisos de grupo según necesites
def supplier_create_view(request):
    if request.method == 'POST':
        form = SupplierForm(request.POST)
        if form.is_valid():
            supplier = form.save()
            messages.success(request, _('Supplier "%(name)s" created successfully.') % {'name': supplier.name})
            return redirect('invoicing:supplier_list')
    else:
        form = SupplierForm()
    return render(request, 'invoicing/supplier_form.html', {'form': form, 'title': _('Create New Supplier')})

@login_required
@group_required('Admin', 'InventoryManager') # Ajusta los permisos de grupo según necesites
def supplier_update_view(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    if request.method == 'POST':
        form = SupplierForm(request.POST, instance=supplier)
        if form.is_valid():
            form.save()
            messages.success(request, _('Supplier "%(name)s" updated successfully.') % {'name': supplier.name})
            return redirect('invoicing:supplier_detail', pk=supplier.pk)
    else:
        form = SupplierForm(instance=supplier)
    return render(request, 'invoicing/supplier_form.html', {'form': form, 'object': supplier, 'title': _('Edit %s') % supplier.name})

@login_required
@group_required('Admin') # Eliminar suele ser una acción más restringida
def supplier_delete_view(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    if request.method == 'POST': # Confirmación de borrado
        try:
            supplier_name = supplier.name # Guardar nombre para el mensaje
            supplier.delete()
            messages.success(request, _('Supplier "%(name)s" deleted successfully.') % {'name': supplier_name})
            return redirect('invoicing:supplier_list')
        except models.ProtectedError as e:
            messages.error(request, _("Cannot delete supplier '%(name)s' as it is linked to other records. Details: %(error)s") % {'name': supplier.name, 'error': e})
            return redirect('invoicing:supplier_detail', pk=pk)
        except Exception as e:
            messages.error(request, _("An unexpected error occurred while trying to delete supplier '%(name)s'. Error: %(error)s") % {'name': supplier.name, 'error': e})
            return redirect('invoicing:supplier_detail', pk=pk)
    # Para peticiones GET, se muestra la plantilla de confirmación
    return render(request, 'invoicing/supplier_confirm_delete.html', {'object': supplier, 'title': _('Delete Supplier: %s') % supplier.name})



