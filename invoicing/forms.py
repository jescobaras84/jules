# invoicing/forms.py
from django import forms
from django.forms import inlineformset_factory
from .models import (
    Product, Invoice, InvoiceItem, 
    PurchaseOrder, PurchaseOrderItem,
    Customer, Supplier # CRITICAL: Ensure Customer and Supplier are imported
)
from decimal import Decimal

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'current_stock_ml', 'minimum_stock_ml']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'current_stock_ml': forms.NumberInput(attrs={'class': 'form-control'}),
            'minimum_stock_ml': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class AddStockForm(forms.Form):
    product = forms.ModelChoiceField(queryset=Product.objects.all(), widget=forms.Select(attrs={'class': 'form-control'}))
    quantity_ml_added = forms.DecimalField(min_value=Decimal('0.01'), label="Quantity (ml) to Add", widget=forms.NumberInput(attrs={'class': 'form-control'}))
    notes = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}), required=False)

class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ['customer'] # Changed from customer_name

class InvoiceItemForm(forms.ModelForm):
    product = forms.ModelChoiceField(queryset=Product.objects.all(), widget=forms.Select(attrs={'class': 'form-control product-select'}))
    quantity_input = forms.DecimalField(label="Quantity", min_value=Decimal('0.01'), widget=forms.NumberInput(attrs={'class': 'form-control quantity-input'}))
    unit_of_measure = forms.ChoiceField(choices=[('ml', 'Milliliters'), ('litre', 'Liters'), ('gallon', 'Gallons')], widget=forms.Select(attrs={'class': 'form-control unit-select'}))
    unit_price = forms.DecimalField(label="Unit Price (for the selected unit e.g. price per Gallon)", min_value=Decimal('0.00'), widget=forms.NumberInput(attrs={'class': 'form-control unit-price'}))

    class Meta:
        model = InvoiceItem
        fields = ['product', 'quantity_input', 'unit_of_measure', 'unit_price']

InvoiceItemFormSet = inlineformset_factory(
    Invoice,
    InvoiceItem,
    form=InvoiceItemForm,
    fields=['product', 'quantity_input', 'unit_of_measure', 'unit_price'],
    extra=1,
    can_delete=True,
    widgets={ 
        'product': forms.Select(attrs={'class': 'form-control product-select'}),
        'quantity_input': forms.NumberInput(attrs={'class': 'form-control quantity-input'}),
        'unit_of_measure': forms.Select(attrs={'class': 'form-control unit-select'}),
        'unit_price': forms.NumberInput(attrs={'class': 'form-control unit-price'}),
    }
)

class PurchaseOrderForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrder
        fields = ['supplier'] # Changed from supplier_name

class PurchaseOrderItemForm(forms.ModelForm):
    product = forms.ModelChoiceField(queryset=Product.objects.all(), widget=forms.Select(attrs={'class': 'form-control product-select'}))
    quantity_input = forms.DecimalField(label="Quantity", min_value=Decimal('0.01'), widget=forms.NumberInput(attrs={'class': 'form-control quantity-input'}))
    unit_of_measure = forms.ChoiceField(
        choices=[
            ('ml', 'Milliliters'),
            ('litre', 'Liters'),
            ('gallon', 'Gallons'),
            ('pichinga', 'Pichingas')
        ], 
        widget=forms.Select(attrs={'class': 'form-control unit-select'})
    )
    unit_cost = forms.DecimalField(label="Unit Cost (for selected unit)", min_value=Decimal('0.00'), widget=forms.NumberInput(attrs={'class': 'form-control unit-cost'}))

    class Meta:
        model = PurchaseOrderItem
        fields = ['product', 'quantity_input', 'unit_of_measure', 'unit_cost']

PurchaseOrderItemFormSet = inlineformset_factory(
    PurchaseOrder,
    PurchaseOrderItem,
    form=PurchaseOrderItemForm,
    fields=['product', 'quantity_input', 'unit_of_measure', 'unit_cost'],
    extra=1,
    can_delete=True
)

# === Customer and Supplier Forms ===

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['name', 'id_type', 'id_number', 'address', 'email', 'phone', 'secondary_email', 'secondary_phone', 'notes_cxc']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'id_type': forms.Select(attrs={'class': 'form-control'}),
            'id_number': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'secondary_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'secondary_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'notes_cxc': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ['name', 'id_type', 'id_number', 'address', 'email', 'phone', 'secondary_email', 'secondary_phone', 'notes_cxp']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'id_type': forms.Select(attrs={'class': 'form-control'}),
            'id_number': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'secondary_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'secondary_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'notes_cxp': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class CustomerQuickAddForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['name', 'id_type', 'id_number', 'email', 'phone']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'id_type': forms.Select(attrs={'class': 'form-control form-control-sm'}),
            'id_number': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'email': forms.EmailInput(attrs={'class': 'form-control form-control-sm'}),
            'phone': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
        }

class SupplierQuickAddForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ['name', 'id_type', 'id_number', 'email', 'phone']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'id_type': forms.Select(attrs={'class': 'form-control form-control-sm'}),
            'id_number': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'email': forms.EmailInput(attrs={'class': 'form-control form-control-sm'}),
            'phone': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
        }
