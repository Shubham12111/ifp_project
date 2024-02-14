from django.contrib import admin
from django.urls import path
from django.contrib.auth.decorators import login_required
from .views import *
from .site_address import *
from .contact_person import *
from .sor_views import *

urlpatterns = [
    path('list/', CustomerListView.as_view(), name='customer_list'),
    path('add/', CustomerAddView.as_view(), name='customer_add'),
    path('edit/<int:customer_id>/', CustomerUpdateView.as_view(), name='customer_edit'),
    path('detail/<int:customer_id>/', CustomerDetailView.as_view(), name='customer_detail'),

    path('delete/<int:pk>/',CustomerDeleteView.as_view(),name='delete_customer'),
    path('convert_contact/<int:contact_id>/', ConvertToCustomerView.as_view(), name='convert_to_customer'),


    path('billing_address/<int:customer_id>/', CustomerBillingAddressView.as_view(), name='customer_billing_address'),
    path('billing_address/edit/<int:customer_id>/<int:address_id>/', CustomerBillingAddressView.as_view(), name='customer_billing_address_edit'),
    path('billing_address/delete/<int:customer_id>/<int:address_id>/', CustomerRemoveBillingAddressView.as_view(), name='customer_billing_address_delete'),
    
    path('site_address/<int:customer_id>/', CustomerSiteAddressView.as_view(), name='customer_site_address'),
    path('site_address/edit/<int:customer_id>/<int:address_id>/', CustomerSiteAddressView.as_view(), name='customer_site_address_edit'),
    path('site_address/delete/<int:customer_id>/<int:address_id>/', CustomerRemoveSiteAddressView.as_view(), name='customer_site_address_delete'),
    path('site_address/view/<int:customer_id>/<int:address_id>/', CustomerSiteDetailView.as_view(), name='customer_site_address_view'),
    
    path('contact_person/<int:customer_id>/', CustomerContactPersonView.as_view(), name='customer_contact_person'),
    path('contact_person/edit/<int:customer_id>/<int:address_id>/', CustomerContactPersonView.as_view(), name='customer_contact_person_edit'),
    path('contact_person/view/<int:customer_id>/<int:address_id>/', CustomerContactPersonDetailView.as_view(), name='customer_contact_person_view'),
    path('contact_person/delete/<int:customer_id>/<int:address_id>/', CustomerRemoveContactPersonView.as_view(), name='customer_contact_person_delete'),
    path('billing_address_info/', BillingAddressInfoView.as_view(), name="billing_address_info"),
    path('export_csv/', ExportCSVView.as_view(), name='export_csv'),

    path('customers/sor/', CSSORCustomerListView.as_view(), name='cs_cs_sor_customers_list'),
    
    path('sor/<int:customer_id>/', CSSORListView.as_view(), name='cs_customer_sor_list'),
    path('sor/add/<int:customer_id>/', CSSORAddView.as_view(), name='cs_add_sor_customer'),
    path('sor/import_csv_sor/<int:customer_id>/', CSSORCSVView.as_view(), name='cs_import_csv_sor'),
    
    path('sor/<int:customer_id>/edit/<int:sor_id>/', CSSORUpdateView.as_view(), name='cs_edit_sor_customer'),
    path('view_sor_customer/<int:sor_id>/', CSSORDetailView.as_view(), name='cs_view_sor_customer'),
    path('sor/delete/<int:sor_id>/', CSSORDeleteView.as_view(), name='cs_delete_sor'),
    path('sor/delete/document/<int:customer_id>/<int:sor_id>/<int:document_id>', CSSORRemoveImageView.as_view(), name='cs_delete_sor_document'),

    path('customer/<int:customer_id>/fra-list/', customer_fra_list, name='customer_fra_list'),

]


