from typing import Any
from django.contrib import admin
from django.db.models.query import QuerySet
from django.http import HttpRequest
from .models import BillingAddress, SiteAddress, ContactPerson, CustomerMeta


@admin.register(CustomerMeta)
class CustomerMetaAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'user_id', 'company_registration_number')

    def delete_model(self, request: HttpRequest, obj: CustomerMeta) -> None:
        """
        Deletes the CustomerMeta instance along with its associated user account.

        Arguments:
            self: The instance of the class.
            request (HttpRequest): The HTTP request object.
            obj (CustomerMeta): The CustomerMeta instance to be deleted.

        Returns:
            None

        Raises:
            None
        """
        # Check if the CustomerMeta instance has an associated contact persons
        if obj.contactperson_set.exists():
            for contact_person in obj.contactperson_set.all():
                contact_person.user.delete() # Delete the associated Contact User Accounts
            
            obj.contactperson_set.all().delete()

        # Check if the CustomerMeta instance has an associated user account
        if obj.user_id:
            obj.user_id.delete()  # Delete the associated user account

        return super().delete_model(request, obj)  # Call the superclass method to complete the deletion process
        
    def delete_queryset(self, request: HttpRequest, queryset: QuerySet[CustomerMeta]) -> None:
        """
        Deletes the queryset of CustomerMeta instances along with associated user accounts.

        Arguments:
            self: The instance of the class.
            request (HttpRequest): The HTTP request object.
            queryset (QuerySet[CustomerMeta]): The queryset of CustomerMeta instances to be deleted.

        Returns:
            None

        Raises:
            None
        """
        # Iterate over each customer in the queryset
        for customer in queryset:
            if customer.contactperson_set.exists():
                for contact_person in customer.contactperson_set.all():
                    contact_person.user.delete() # Delete the associated Contact User Accounts
                
                customer.contactperson_set.all().delete()
            
            if customer.user_id:
                customer.user_id.delete()  # Delete the associated user account

        return super().delete_queryset(request, queryset)  # Call the superclass method to complete the deletion process


class BillingAddressAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'vat_number', 'place_to_supply', 'created_at', 'updated_at')

class SiteAddressAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'site_name',  'created_at', 'updated_at')
    search_fields = ('site_name', 'post_code')  # Add fields for searching

class ContactPersonAdmin(admin.ModelAdmin):
    list_display = ('get_customer' ,'get_first_name' ,'get_last_name' ,'get_email' ,'get_phone_number' ,'created_at' ,'updated_at')

    def get_customer(self, obj):
        """
        Retrieves the customer name associated with the contact person.

        Arguments:
            self: The instance of the class.
            obj: The ContactPerson instance.

        Returns:
            str: The name of the customer associated with the contact person.
        """
        return f'{obj.customer}'

    def get_first_name(self, obj):
        """
        Retrieves the first name of the user associated with the contact person.

        Arguments:
            self: The instance of the class.
            obj: The ContactPerson instance.

        Returns:
            str: The first name of the user associated with the contact person.
        """
        return f'{obj.user.first_name}'

    def get_last_name(self, obj):
        """
        Retrieves the last name of the user associated with the contact person.

        Arguments:
            self: The instance of the class.
            obj: The ContactPerson instance.

        Returns:
            str: The last name of the user associated with the contact person.
        """
        return f'{obj.user.last_name}'

    def get_email(self, obj):
        """
        Retrieves the email address of the user associated with the contact person.

        Arguments:
            self: The instance of the class.
            obj: The ContactPerson instance.

        Returns:
            str: The email address of the user associated with the contact person.
        """
        return f'{obj.user.email}'

    def get_phone_number(self, obj):
        """
        Retrieves the phone number of the user associated with the contact person.

        Arguments:
            self: The instance of the class.
            obj: The ContactPerson instance.

        Returns:
            str: The phone number of the user associated with the contact person.
        """
        return f'{obj.user.phone_number}'

    # Customize the display names of the functions in the admin interface
    get_customer.short_description = 'Customer'
    get_first_name.short_description = 'First Name'
    get_last_name.short_description = 'Last Name'
    get_email.short_description = 'Email'
    get_phone_number.short_description = 'Phone Number'
    
admin.site.register(BillingAddress, BillingAddressAdmin)
admin.site.register(SiteAddress, SiteAddressAdmin)
admin.site.register(ContactPerson, ContactPersonAdmin)