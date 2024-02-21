from django.urls import path
from invoice_management.views import (
    ShowInvoiceView,
    CreateInvoiceView,
    EditInvoiceView,
    DeleteInvoiceView,
    SendInvoiceToCustomerView,
    MarkAsPaidInvoiceView
)

urlpatterns = [
    path('customer/<int:customer_id>/invoice/<int:pk>/', ShowInvoiceView.as_view(), name='view_customer_invoice'),

    path('customer/<int:customer_id>/quotation/<int:quotation_id>/', CreateInvoiceView.as_view(), name='create_customer_invoice_for_a_quotation'),
    path('customer/<int:customer_id>/invoice/<int:pk>/edit/', EditInvoiceView.as_view(), name='edit_customer_invoice'),

    path('customer/<int:customer_id>/invoice/<int:pk>/delete/', DeleteInvoiceView.as_view(), name='delete_customer_invoice'),

    path('customer/<int:customer_id>/invoice/<int:pk>/send-to-customer/', SendInvoiceToCustomerView.as_view(), name='send_invoice_to_customer'),
    path('customer/<int:customer_id>/invoice/<int:pk>/mark-as-paid/', MarkAsPaidInvoiceView.as_view(), name='mark_invoice_as_paid'),
]   
