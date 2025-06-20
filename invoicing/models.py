from django.db import models
from django.contrib.auth.models import AbstractUser, Group as DjangoGroup, Permission as DjangoPermission
from django.utils.translation import gettext_lazy as _

# It's often better to extend Django's User model if significant custom fields are needed.
# For now, we'll assume the built-in User model is sufficient for username/password.
# We will create a separate Role model that can be linked to Django's Group for simplicity,
# or used independently if more complex role logic is needed later.

class Role(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

# We can link our custom User to Roles via a ManyToManyField or ForeignKey if needed,
# or utilize Django's Group model and link Role to it.
# For simplicity in this step, Role is standalone. We'll integrate with User/Group later.

class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    # Store stock in smallest unit (ml)
    current_stock_ml = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    minimum_stock_ml = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    # Add created_at and updated_at fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def is_low_stock(self):
        return self.current_stock_ml < self.minimum_stock_ml

    def __str__(self):
        return f"{self.name} ({self.current_stock_ml} ml)"

class Invoice(models.Model):
    # Link to User model (e.g., salesperson who created the invoice)
    # user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    # customer_name = models.CharField(max_length=255) # Simplified customer details for now
    customer = models.ForeignKey('Customer', on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("Customer"))
    invoice_date = models.DateTimeField(auto_now_add=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    # Add created_at and updated_at fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        display_name = self.customer.name if self.customer else "N/A"
        return f"Invoice {self.id} for {display_name} on {self.invoice_date.strftime('%Y-%m-%d')}"

class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.PROTECT) # Prevent deleting product if in an invoice
    quantity_ml = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2) # Price per ml, or per unit sold (e.g. price per bottle)
    # The definition of unit_price needs clarification: is it price per ml, or price per standard unit (gallon/liter) sold?
    # Assuming price for the quantity_ml sold for now.
    line_total = models.DecimalField(max_digits=10, decimal_places=2)

    def save(self, *args, **kwargs):
        self.line_total = self.quantity_ml * self.unit_price # Or appropriate calculation based on unit_price definition
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.quantity_ml} ml of {self.product.name} for invoice {self.invoice.id}"

class PurchaseOrder(models.Model):
    # user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True) # User who created PO
    # supplier_name = models.CharField(max_length=255) # Simplified supplier details
    supplier = models.ForeignKey('Supplier', on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("Supplier"))
    order_date = models.DateTimeField(auto_now_add=True)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_fulfilled = models.BooleanField(default=False)
    # Add created_at and updated_at fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        display_name = self.supplier.name if self.supplier else "N/A"
        return f"PO {self.id} from {display_name} on {self.order_date.strftime('%Y-%m-%d')}"

class PurchaseOrderItem(models.Model):
    purchase_order = models.ForeignKey(PurchaseOrder, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity_ml = models.DecimalField(max_digits=10, decimal_places=2)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2) # Cost per ml, or per unit bought
    line_total = models.DecimalField(max_digits=10, decimal_places=2)

    def save(self, *args, **kwargs):
        self.line_total = self.quantity_ml * self.unit_cost
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.quantity_ml} ml of {self.product.name} for PO {self.purchase_order.id}"

class Customer(models.Model):
    ID_TYPE_CHOICES = [
        ('juridica', _('Cédula Jurídica')),
        ('fisica', _('Cédula Física')),
        ('dimex', _('DIMEX')),
        ('otro', _('Otro (Especificar en notas)')),
    ]

    name = models.CharField(_("Name or Company Name"), max_length=255)
    id_type = models.CharField(_("ID Type"), max_length=10, choices=ID_TYPE_CHOICES, default='fisica')
    id_number = models.CharField(_("ID Number"), max_length=50, blank=True, null=True, help_text=_("Leave blank if not applicable or using 'Otro' ID type"))

    address = models.TextField(_("Physical Address"), blank=True, null=True)
    email = models.EmailField(_("Primary Email"), max_length=254, blank=True, null=True)
    phone = models.CharField(_("Primary Phone"), max_length=30, blank=True, null=True)
    secondary_email = models.EmailField(_("Secondary Email"), max_length=254, blank=True, null=True)
    secondary_phone = models.CharField(_("Secondary Phone"), max_length=30, blank=True, null=True)

    notes_cxc = models.TextField(_("Notes (Accounts Receivable)"), blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Customer")
        verbose_name_plural = _("Customers")
        ordering = ['name']

class Supplier(models.Model):
    ID_TYPE_CHOICES = [
        ('juridica', _('Cédula Jurídica')),
        ('fisica', _('Cédula Física')),
        ('dimex', _('DIMEX')),
        ('otro', _('Otro (Especificar en notas)')),
    ]

    name = models.CharField(_("Name or Company Name"), max_length=255)
    id_type = models.CharField(_("ID Type"), max_length=10, choices=ID_TYPE_CHOICES, default='juridica')
    id_number = models.CharField(_("ID Number"), max_length=50, blank=True, null=True, help_text=_("Leave blank if not applicable or using 'Otro' ID type"))

    address = models.TextField(_("Physical Address"), blank=True, null=True)
    email = models.EmailField(_("Primary Email"), max_length=254, blank=True, null=True)
    phone = models.CharField(_("Primary Phone"), max_length=30, blank=True, null=True)
    secondary_email = models.EmailField(_("Secondary Email"), max_length=254, blank=True, null=True)
    secondary_phone = models.CharField(_("Secondary Phone"), max_length=30, blank=True, null=True)

    notes_cxp = models.TextField(_("Notes (Accounts Payable)"), blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Supplier")
        verbose_name_plural = _("Suppliers")
        ordering = ['name']
