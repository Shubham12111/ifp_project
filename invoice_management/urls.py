from django.urls import path
from invoice_management.views import (
    ShowInvoiceView,
    CreateInvoiceView,
    EditInvoiceView,
    DeleteInvoiceView,
)

urlpatterns = [
    path('customer/<int:customer_id>/invoice/<int:pk>/', ShowInvoiceView.as_view(), name='view_customer_invoice'),

    path('customer/<int:customer_id>/quotation/<int:quotation_id>/', CreateInvoiceView.as_view(), name='create_customer_invoice_for_a_quotation'),
    path('customer/<int:customer_id>/invoice/<int:pk>/edit/', EditInvoiceView.as_view(), name='edit_customer_invoice'),

    path('customer/<int:customer_id>/invoice/<int:pk>/delete', DeleteInvoiceView.as_view(), name='delete_customer_invoice'),
]   
