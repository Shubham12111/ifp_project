from django.db import models
from stock_management.models import Vendor, InventoryLocation, Item
from customer_management.models import SiteAddress
from authentication.models import User
from django.db.models import Sum

# Define choices for the status field
STATUS_CHOICES = [
    ('pending', 'Pending'),
    ('sent_for_approval', 'Sent for Approval'),
    ('approved', 'Approved'),
    ('partially_completed', 'Partially completed'),
    ('completed', 'Completed'),
]

LOCATION_TYPE_CHOICES = [('site address', 'Site Address'), ('warehouse', 'Warehouse')]

class PurchaseOrder(models.Model):
    """
    Represents a Purchase Order in the system.
    """
    po_number = models.CharField(max_length=50, unique=True)
    vendor_id = models.ForeignKey(Vendor, on_delete=models.CASCADE)
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    inventory_location_id = models.ForeignKey(InventoryLocation, on_delete=models.CASCADE, null=True, blank=True)
    site_address = models.ForeignKey(SiteAddress, on_delete=models.CASCADE, null=True, blank=True)
    location_type = models.CharField(max_length=20, choices=LOCATION_TYPE_CHOICES, default='warehouse')
    sub_total = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    notes = models.TextField(null=True, blank=True)
    approval_notes = models.TextField(null=True, blank=True)
    document = models.CharField(max_length=255, null=True, blank=True)
    created_by = models.ForeignKey(User, related_name='created_orders', on_delete=models.CASCADE)
    approved_by = models.ForeignKey(User, related_name='approved_orders', on_delete=models.CASCADE, null=True)
    
    approved_at = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.po_number
    
    class Meta:
        ordering =['id']

class PurchaseOrderItem(models.Model):
    """
    Represents an item in a Purchase Order.
    """
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
    
    class Meta:
        ordering =['id']

class PurchaseOrderInvoice(models.Model):
    """
    Represents an invoice associated with a Purchase Order.
    """
    purchase_order_id = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE)
    invoice_number = models.CharField(max_length=50)
    invoice_date = models.DateField()
    invoice_pdf_path = models.CharField(max_length=200, null=True, blank=True)
    comments = models.TextField(max_length=200, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.invoice_number

    def calculate_received_inventory(self):
        """
        Calculate the total received inventory for this invoice.
        """
        received_inventory = PurchaseOrderReceivedInventory.objects.filter(
            purchase_order_invoice_id=self
        ).aggregate(total_received_inventory=Sum('received_inventory'))['total_received_inventory']

        return received_inventory or 0
    
class PurchaseOrderReceivedInventory(models.Model):
    """
    Represents received inventory associated with a Purchase Order Invoice.
    """
    purchase_order_invoice_id = models.ForeignKey(PurchaseOrderInvoice, on_delete=models.CASCADE)
    purchase_order_item_id = models.ForeignKey(PurchaseOrderItem, on_delete=models.CASCADE)
    received_inventory = models.PositiveIntegerField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Received Inventory for {self.purchase_order_item_id}"

    class Meta:
        ordering =['id']