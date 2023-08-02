from django.contrib import admin
from django.urls import path
from django.contrib.auth.decorators import login_required
from .views import *
from .site_address import *
from .contact_person import *

urlpatterns = [
    path('list/', CustomerListView.as_view(), name='customer_list'),
    path('add/', CustomerAddView.as_view(), name='customer_add'),
    path('edit/<int:customer_id>/', CustomerUpdateView.as_view(), name='customer_edit'),
    path('billing_address/<int:customer_id>/', CustomerBillingAddressView.as_view(), name='customer_billing_address'),
    path('billing_address/edit/<int:customer_id>/<int:address_id>/', CustomerBillingAddressView.as_view(), name='customer_billing_address_edit'),
    path('billing_address/delete/<int:customer_id>/<int:address_id>/', CustomerRemoveBillingAddressView.as_view(), name='customer_billing_address_delete'),
    
    path('site_address/<int:customer_id>/', CustomerSiteAddressView.as_view(), name='customer_site_address'),
    path('site_address/edit/<int:customer_id>/<int:address_id>/', CustomerSiteAddressView.as_view(), name='customer_site_address_edit'),
    path('site_address/delete/<int:customer_id>/<int:address_id>/', CustomerRemoveSiteAddressView.as_view(), name='customer_site_address_delete'),
    
    path('contact_person/<int:customer_id>/', CustomerContactPersonView.as_view(), name='customer_contact_person'),
    path('contact_person/edit/<int:customer_id>/<int:address_id>/', CustomerContactPersonView.as_view(), name='customer_contact_person_edit'),
    path('contact_person/delete/<int:customer_id>/<int:address_id>/', CustomerRemoveContactPersonView.as_view(), name='customer_contact_person_delete'),
]


