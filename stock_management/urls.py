from django.contrib import admin
from django.urls import path
from .views import *
from .category import *


urlpatterns = [
   path('vendor/list/', VendorListView.as_view(), name='vendor_list'),
   path('vendor/add/', VendorAddView.as_view(), name='vendor_add'),
   path('vendor/edit/<int:vendor_id>/', VendorUpdateView.as_view(), name='vendor_edit'),
   path('vendor/delete/<int:pk>/',VendorDeleteView.as_view(),name='delete_vendor'),
   path('vendor/billing/<int:vendor_id>/', VendorBillingDetailView.as_view(), name='vendor_billing_detail'),
   
   path('category/list/', CategoryListView.as_view(), name='category_list'),
   path('category/add/', CategoryAddView.as_view(), name='category_add'),
   path('category/edit/<int:category_id>/', CategoryUpdateView.as_view(), name='category_edit'),
   path('category/delete/<int:category_id>/',CategoryDeleteView.as_view(),name='category_delete'),

]
