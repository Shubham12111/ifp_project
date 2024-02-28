from django.contrib import admin
from .models import BillingAddress, SiteAddress, ContactPerson


class BillingAddressAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'vat_number', 'place_to_supply', 'created_at', 'updated_at')

class SiteAddressAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'site_name',  'created_at', 'updated_at')
    search_fields = ('site_name', 'post_code')  # Add fields for searching

# class ContactPersonAdmin(admin.ModelAdmin):
#     list_display = ('user_id' ,'first_name' ,'last_name' ,'email' ,'phone_number' ,'created_at' ,'updated_at')
    
admin.site.register(BillingAddress, BillingAddressAdmin)
admin.site.register(SiteAddress, SiteAddressAdmin)
# admin.site.register(ContactPerson, ContactPersonAdmin)