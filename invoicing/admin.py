from django.contrib import admin
from .models import Role, Product, Invoice, InvoiceItem, PurchaseOrder, PurchaseOrderItem

admin.site.register(Role)
admin.site.register(Product)
admin.site.register(Invoice)
admin.site.register(InvoiceItem)
admin.site.register(PurchaseOrder)
admin.site.register(PurchaseOrderItem)
