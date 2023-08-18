from django.db import models
from stock_management.models import Vendor, InventoryLocation,Item
from authentication.models import User
from django.db.models import Sum

# Define choices for the status field
STATUS_CHOICES = [
    ('pending', 'Pending'),
    ('sent_for_approval', 'Sent for Approval'),
    ('approved', 'Approved'),
    ('rejected', 'Rejected'),
    # Add more status choices as needed
]


class PurchaseOrder(models.Model):
    po_number = models.CharField(max_length=50, unique=True)
    vendor_id = models.ForeignKey(Vendor, on_delete=models.CASCADE)
    inventory_location_id = models.ForeignKey(InventoryLocation, on_delete=models.CASCADE)
    order_date = models.DateField()
    due_date = models.DateField()
    sub_total = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    notes = models.TextField(null=True, blank=True)
    approval_notes = models.TextField(null=True, blank=True)
    document = models.CharField(max_length=255,null=True, blank=True)
    created_by = models.ForeignKey(User, related_name='created_orders', on_delete=models.CASCADE)
    approved_by = models.ForeignKey(User, related_name='approved_orders', on_delete=models.CASCADE, null=True)
    
    approved_at = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.po_number
    

class PurchaseOrderItem(models.Model):
    purchase_order_id = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    item_name = models.CharField(max_length=100)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    row_total = models.DecimalField(max_digits=10, decimal_places=2)
    received_quantity = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.item_name} - {self.purchase_order_id.po_number}"

class PurchaseOrderInvoice(models.Model):
    purchase_order_id = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE)
    invoice_number = models.CharField(max_length=50)
    invoice_date = models.DateField()
    invoice_pdf_path = models.CharField(max_length=200, null=True, blank=True)
    comments = models.TextField(max_length=200, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.invoice_id  # Display the invoice_id as the string representation

class PurchaseOrderReceivedInventory(models.Model):
    purchase_order_invoice_id = models.ForeignKey(PurchaseOrderInvoice, on_delete=models.CASCADE)
    purchase_order_item_id = models.ForeignKey(PurchaseOrderItem, on_delete=models.CASCADE)
    received_inventory = models.PositiveIntegerField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Received Inventory for {self.purchase_order_item_id}"

    def get_cumulative_received_quantity(self):
        return PurchaseOrderReceivedInventory.objects.filter(purchase_order_item_id=self.purchase_order_item_id).exclude(id=self.id).aggregate(Sum('received_inventory'))['received_inventory__sum'] or 0