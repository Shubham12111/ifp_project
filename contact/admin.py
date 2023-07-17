from django.contrib import admin
from .models import Contact, ContactType

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'phone_number', 'contact_type', 'job_title', 'company', 'address', 'city', 'state', 'pincode', 'country', 'created_at', 'updated_at']
    list_filter = ['contact_type']
    search_fields = ['name', 'email']

@admin.register(ContactType)
class ContactTypeAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']