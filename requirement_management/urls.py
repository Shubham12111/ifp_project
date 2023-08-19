from django.contrib import admin
from django.urls import path
from django.contrib.auth.decorators import login_required
from .views import *

urlpatterns = [
    path('list/', RequirementListView.as_view(), name='requirement_list'),
    path('add/', RequirementAddView.as_view(), name='requirement_add'),
    path('view/<int:pk>/', RequirementDetailView.as_view(), name='requirement_view'),
    path('edit/<int:pk>/', RequirementUpdateView.as_view(), name='requirement_edit'),
    path('delete/<int:pk>/',RequirementDeleteView.as_view(),name='requirement_delete'),
    path('delete/document/<int:requirement_id>/<int:document_id>/', login_required(RequirementRemoveDocumentView.as_view()), name='remove_requirement_document'),
    
    path('defects/<int:requirement_id>/', RequirementDefectView.as_view(), name='requirement_defects'),
    path('defects/edit/<int:requirement_id>/<int:pk>/', RequirementDefectView.as_view(), name='requirement_defect_update'),
    path('defect/detail/<int:defect_id>/', RequirementDefectDetailView.as_view(), name='requirement_defect_detail'),
    path('defect/detail/edit/response/<int:defect_id>/<int:pk>/', RequirementDefectDetailView.as_view(), name='requirement_defect_edit_response'),
     path('defect/detail/delete/response/<int:defect_id>/<int:pk>/', RequirementDefectResponseDeleteView.as_view(), name='requirement_defect_delete_response'),
    
    
    path('defects/delete/<int:pk>/', RequirementDefectDeleteView.as_view(), name='requirement_defect_delete'),
    path('defects/delete/document/<int:defect_id>/<int:pk>/', login_required(RequirementDefectRemoveDocumentView.as_view()), name='remove_requirement_defect_document'),


]