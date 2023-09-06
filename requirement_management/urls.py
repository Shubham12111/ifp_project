from django.contrib import admin
from django.urls import path
from django.contrib.auth.decorators import login_required
from .views import *

urlpatterns = [
    path('customers/', RequirementCustomerListView.as_view(), name='customers_list'),
    path('customers/<int:customer_id>/list/', RequirementListView.as_view(), name='customer_requirement_list'),
    path('customers/<int:customer_id>/add/', RequirementAddView.as_view(), name='customer_requirement_add'),
    path('customers/<int:customer_id>/view/<int:pk>/', RequirementDetailView.as_view(), name='customer_requirement_view'),
    path('customers/<int:customer_id>/edit/<int:pk>/', RequirementUpdateView.as_view(), name='customer_requirement_edit'),
    path('customers/<int:customer_id>/delete/<int:pk>/',RequirementDeleteView.as_view(),name='customer_requirement_delete'),
    path('delete/document/<int:requirement_id>/<int:document_id>/', login_required(RequirementRemoveDocumentView.as_view()), name='remove_requirement_document'),
    
    path('customers/<int:customer_id>/<int:requirement_id>/defects/', RequirementDefectView.as_view(), name='customer_requirement_defects'),
    path('customers/<int:customer_id>/defects/edit/<int:requirement_id>/<int:pk>/', RequirementDefectView.as_view(), name='customer_requirement_defect_update'),
    path('customers/<int:customer_id>/<int:requirement_id>/defect/detail/<int:defect_id>/', RequirementDefectDetailView.as_view(), name='customer_requirement_defect_detail'),

    path('defects/delete/<int:pk>/', RequirementDefectDeleteView.as_view(), name='requirement_defect_delete'),
    path('defects/delete/document/<int:defect_id>/<int:pk>/', login_required(RequirementDefectRemoveDocumentView.as_view()), name='remove_requirement_defect_document'),

    path('quantity_surveyor/add/<int:customer_id>/',RequirementQSAddView.as_view() , name='add_quantity_surveyor')
]