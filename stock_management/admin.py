from django.contrib import admin

from . models import Vendor,VendorContactPerson,Item,ItemImage,InventoryLocation,Inventory
 


# Register your models here.
class VendorAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'first_name','last_name','email','phone_number', 'created_at', 'updated_at')
    search_fields = ('email',)  # Add fields for searching


class VendorContactPersonAdmin(admin.ModelAdmin):
    list_display = ('salutation', 'first_name','last_name','email','phone_number', 'created_at', 'updated_at')
    search_fields = ('first_name','last_name','email')  # Add fields for searching



admin.site.register(Vendor, VendorAdmin)
admin.site.register(VendorContactPerson, VendorContactPersonAdmin)
admin.site.register(Item)
admin.site.register(ItemImage)
admin.site.register(InventoryLocation)
admin.site.register(Inventory)

