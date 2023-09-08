from django.contrib import admin
from django.urls import path
from .views import *

urlpatterns = [
   path('list/', PurchaseOrderListView.as_view(), name='purchase_order_list'),
   path('add/', PurchaseOrderAddView.as_view(), name='purchase_order_add'),
   path('get_vendor_data/', get_vendor_data, name='get_vendor_data'),
   path('inventory_location/', get_inventory_location_data, name='get_inventory_location_data'),
   path('edit/<int:purchase_order_id>/', PurchaseOrderUpdateView.as_view(), name='purchase_order_edit'),
   # path('delete/<int:purchase_order_id>/', PurchaseDeleteView.as_view(), name='purchase_order_delete'),
   
   path('view/<int:purchase_order_id>/', PurchaseOrderView.as_view(), name='purchase_order_view'),
   path('invoice/<int:purchase_order_id>/', PurchaseOrderConvertToInvoiceView.as_view(), name='purchase_order_convert_to_invoice'),
   path('invoice/view/<int:purchase_order_id>/<int:invoice_id>/', PurchaseOrderInvoiceView.as_view(), name='purchase_order_invoice'),

]
