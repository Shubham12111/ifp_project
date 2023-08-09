from django.contrib import admin
from django.urls import path
from .views import *

urlpatterns = [
   path('list/', VendorListView.as_view(), name='vendor_list'),
   path('add/', VendorAddView.as_view(), name='vendor_add'),
   path('edit/<int:vendor_id>/', VendorUpdateView.as_view(), name='vendor_edit'),
   path('delete/<int:pk>/',VendorDeleteView.as_view(),name='delete_vendor'),
   
   path('billing_detail/<int:vendor_id>/', VendorBillingDetailView.as_view(), name='vendor_billing_detail'),
]
