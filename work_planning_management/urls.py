from .views import *
from django.urls import path
from django.contrib.auth.decorators import login_required



urlpatterns = [
    path('stw_customers/', STWCustomerListView.as_view(), name='stw_customers_list'),
    path('stw_customers/<int:customer_id>/list/', STWRequirementListView.as_view(), name='customer_stw_list'),
    path('stw_customers/<int:customer_id>/add/', STWRequirementAddView.as_view(), name='customer_stw_add'),
    path('stw_customers/<int:customer_id>/edit/<int:pk>/', STWRequirementUpdateView.as_view(), name='customer_stw_edit'),
    path('stw_customers/<int:customer_id>/delete/<int:pk>/',STWRequirementDeleteView.as_view(),name='customer_stw_delete'),
    path('delete/document/<int:stw_id>/<int:document_id>/', login_required(STWRemoveDocumentView.as_view()), name='remove_stw_document'),
    path('<int:customer_id>/view/<int:pk>/', STWDetailView.as_view(), name='customer_stw_view'),
    

   
]