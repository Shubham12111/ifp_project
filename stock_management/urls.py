from django.contrib import admin
from django.urls import path
from .views import *
from .category import *
from .contact_person import *
from .item import *
from .inventory_location import *
from .inventory import *
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


   path('vendor/contact_person/<int:vendor_id>/', VendorContactPersonView.as_view(), name='vendor_contact_person'),
   path('vendor/contact_person/edit/<int:vendor_id>/<int:contact_id>/', VendorContactPersonView.as_view(), name='vendor_contact_person_edit'),
   path('vendor/contact_person/delete/<int:vendor_id>/<int:contact_id>/', VendorRemoveContactPersonView.as_view(), name='vendor_contact_person_delete'),

   path('vendor/remarks/<int:vendor_id>/',VendorRemarkView.as_view(), name='vendor_remarks'),
   
   path('item/list/', ItemListView.as_view(), name='item_list'),
   path('item/add/', ItemAddView.as_view(), name='item_add'),
   path('item/edit/<int:item_id>/', ItemUpdateView.as_view(), name='item_edit'),
   path('item/delete/<int:item_id>/', ItemDeleteView.as_view(), name='item_delete'),
   path('inventory/<int:item_id>/', InventoryView.as_view(), name='inventory_view'),
   path('item/remoev/image/<int:item_id>/<int:pk>/', ItemRemoveImageView.as_view(), name='item_image_remove'),

   
   path('inventory_location/list/', InventoryLocationListView.as_view(), name='inventory_location_list'),
   path('inventory_location/add/', InventoryLocationAddView.as_view(), name='inventory_location_add'),
   path('inventory_location/edit/<int:inventory_location_id>/', InventoryLocationUpdateView.as_view(), name='inventory_location_edit'),
   path('inventory_location/delete/<int:inventory_location_id>/', InventoryLocationDeleteView.as_view(), name='inventory_location_delete'),
   
   path('sor/list/', ItemSorListView.as_view(), name='list_sor'),
   path('sor/add/', ItemSorAddView.as_view(), name='add_sor'),
   
   path('sor/edit/<int:item_id>/', ItemSorUpdateView.as_view(), name='edit_sor'),
   path('sor/delete/<int:item_id>/', ItemSorDeleteView.as_view(), name='delete_sor'),


]
