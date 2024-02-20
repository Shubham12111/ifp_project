from django.contrib import admin
from django.db.models.query import QuerySet
from django.http import HttpRequest

from django_admin_listfilter_dropdown.filters import (
    DropdownFilter, ChoiceDropdownFilter, RelatedDropdownFilter
)

from infinity_fire_solutions.aws_helper import delete_file_from_s3

from invoice_management.models import Invoice
# Register your models here.

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Invoice model.
    """

    list_display = (
        'get_invoice_name', 'get_customer', 'get_user', 'total_amount', 'get_status'
    )

    def get_invoice_name(self, obj):
        """
        Get the name of the Invoice.
        
        Args:
            obj (Invoice): The Invoice instance.

        Returns:
            str: The name of the Invoice.
        """
        return obj.__str__()

    def get_status(self, obj):
        """
        Get the status of the Invoice.
        
        Args:
            obj (Invoice): The Invoice instance.

        Returns:
            str: The status of the Invoice.
        """
        return obj.get_status_display()

    def get_customer(self, obj):
        """
        Get the customer of the Invoice.
        
        Args:
            obj (Invoice): The Invoice instance.

        Returns:
            str: The customer of the Invoice.
        """
        return obj.customer

    def get_user(self, obj):
        """
        Get the creator of the Invoice.
        
        Args:
            obj (Invoice): The Invoice instance.

        Returns:
            str: The creator of the Invoice.
        """
        return obj.user

    get_invoice_name.short_description = 'Name'
    get_status.short_description = 'Status'
    get_customer.short_description = 'Customer'
    get_user.short_description = 'Created By'

    list_filter = (
        ('user', RelatedDropdownFilter),
        ('customer', RelatedDropdownFilter),
        ('status', ChoiceDropdownFilter)
    )
    list_per_page = 20

    search_fields = ('total_amount',)
    search_help_text = 'Search By: Total Amount'

    def delete_queryset(self, request, queryset) -> None:
        """
        Delete a queryset of Invoice instances.
        
        Args:
            request (HttpRequest): The request object.
            queryset (QuerySet): The queryset of Invoice instances to delete.

        Returns:
            None
        """
        for obj in queryset:
            deleted = delete_file_from_s3(obj.pdf_path)
        return super().delete_queryset(request, queryset)

    def delete_model(self, request, obj) -> None:
        """
        Delete a single Invoice instance.
        
        Args:
            request (HttpRequest): The request object.
            obj (Invoice): The Invoice instance to delete.

        Returns:
            None
        """
        deleted = delete_file_from_s3(obj.pdf_path)
        return super().delete_model(request, obj)