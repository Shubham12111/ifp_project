from django import template
from django.db.models import Sum
from purchase_order_management.models import PurchaseOrderReceivedInventory,PurchaseOrderItem
from stock_management.models import Inventory
from collections import defaultdict


register = template.Library()

@register.filter
def calculate_total_received_inventory(order_item):
    # Initialize a variable to store the total received inventory
    total_received_inventory = 0

    # Get all inventory entries for the given order item
    inventory_entries = Inventory.objects.filter(item_id=order_item)

    # Iterate through inventory entries and calculate total received by location
    for inventory_entry in inventory_entries:
        purchase_order_items = PurchaseOrderItem.objects.filter(
            item=order_item,
            purchase_order_id__inventory_location_id=inventory_entry.inventory_location
        )
        total_received_by_location = PurchaseOrderReceivedInventory.objects.filter(
            purchase_order_item_id__in=purchase_order_items
        ).aggregate(total_received_inventory=Sum('received_inventory'))['total_received_inventory']
        
        # Accumulate the received inventory for all locations
        total_received_inventory += total_received_by_location or 0

    return total_received_inventory