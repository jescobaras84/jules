# invoicing/forms.py
from django import forms
from .models import Product

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
    quantity_ml_added = forms.DecimalField(min_value=0.01, label="Quantity (ml) to Add", widget=forms.NumberInput(attrs={'class': 'form-control'}))
    notes = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}), required=False)

from django.forms import inlineformset_factory
from .models import Invoice, InvoiceItem # Product is already imported

class InvoiceForm(forms.ModelForm):
    customer_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    # invoice_date will be auto_now_add
    class Meta:
        model = Invoice
        fields = ['customer_name'] # Add other fields if any

class InvoiceItemForm(forms.ModelForm):
    product = forms.ModelChoiceField(queryset=Product.objects.all(), widget=forms.Select(attrs={'class': 'form-control product-select'}))
    # We'll add quantity and unit fields, then calculate quantity_ml in the view
    quantity_input = forms.DecimalField(label="Quantity", min_value=0.01, widget=forms.NumberInput(attrs={'class': 'form-control quantity-input'}))
    unit_of_measure = forms.ChoiceField(choices=[('ml', 'Milliliters'), ('litre', 'Liters'), ('gallon', 'Gallons')], widget=forms.Select(attrs={'class': 'form-control unit-select'}))
    unit_price = forms.DecimalField(label="Unit Price (for the selected unit e.g. price per Gallon)", min_value=0.00, widget=forms.NumberInput(attrs={'class': 'form-control unit-price'}))

    class Meta:
        model = InvoiceItem
        fields = ['product', 'quantity_input', 'unit_of_measure', 'unit_price'] # quantity_ml will be calculated

# quantity_ml will be calculated in the view before saving InvoiceItem
# line_total will also be calculated in the view or model's save method.

InvoiceItemFormSet = inlineformset_factory(
    Invoice,
    InvoiceItem,
    form=InvoiceItemForm,
    fields=['product', 'quantity_input', 'unit_of_measure', 'unit_price'],
    extra=1, # Number of empty forms to display
    can_delete=True,
    widgets={ # These widgets apply if not overridden by InvoiceItemForm's widgets.
        'product': forms.Select(attrs={'class': 'form-control product-select'}),
        'quantity_input': forms.NumberInput(attrs={'class': 'form-control quantity-input'}),
        'unit_of_measure': forms.Select(attrs={'class': 'form-control unit-select'}),
        'unit_price': forms.NumberInput(attrs={'class': 'form-control unit-price'}),
    }
)

from .models import PurchaseOrder, PurchaseOrderItem # Product, Invoice, InvoiceItem already imported

class PurchaseOrderForm(forms.ModelForm):
    supplier_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    # order_date will be auto_now_add
    class Meta:
        model = PurchaseOrder
        fields = ['supplier_name'] # Add other fields if any, like expected_delivery_date

class PurchaseOrderItemForm(forms.ModelForm):
    product = forms.ModelChoiceField(queryset=Product.objects.all(), widget=forms.Select(attrs={'class': 'form-control product-select'}))
    # Assuming quantity_ml is what we order, directly in milliliters for simplicity with suppliers.
    # If orders are in other units, conversion similar to Invoices would be needed.
    # For this iteration, we'll assume orders are specified in ml.
    quantity_ml = forms.DecimalField(label="Quantity (ml)", min_value=0.01, widget=forms.NumberInput(attrs={'class': 'form-control'}))
    unit_cost = forms.DecimalField(label="Unit Cost (per ml)", min_value=0.00, widget=forms.NumberInput(attrs={'class': 'form-control'}))

    class Meta:
        model = PurchaseOrderItem
        fields = ['product', 'quantity_ml', 'unit_cost']

PurchaseOrderItemFormSet = inlineformset_factory(
    PurchaseOrder,
    PurchaseOrderItem,
    form=PurchaseOrderItemForm,
    fields=['product', 'quantity_ml', 'unit_cost'],
    extra=1,
    can_delete=True
)
