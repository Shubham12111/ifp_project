from django.contrib import admin
from django.urls import path
from .views import *
from .category import *
from .item import *
from .item_sor import *

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
   
   path('item/list/', ItemListView.as_view(), name='item_list'),
   path('item/add/', ItemAddView.as_view(), name='item_add'),
   
   path('item/edit/<int:item_id>/', ItemUpdateView.as_view(), name='item_edit'),
   path('item/delete/<int:item_id>/', ItemDeleteView.as_view(), name='item_delete'),
   
   path('item_sor/list/', ItemSorListView.as_view(), name='item_list_sor'),
   path('item_sor/add/', ItemSorAddView.as_view(), name='item_add_sor'),
   
   path('item_sor/edit/<int:item_id>/', ItemSorUpdateView.as_view(), name='item_edit_sor'),
   path('item_sor/delete/<int:item_id>/', ItemSorDeleteView.as_view(), name='item_delete_sor'),

]
