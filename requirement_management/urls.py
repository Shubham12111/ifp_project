from django.contrib import admin
from django.urls import path
from django.contrib.auth.decorators import login_required
from .views import *

urlpatterns = [
    path('list/', RequirementListView.as_view(), name='requirement_list'),
    path('add/', RequirementAddView.as_view(), name='requirement_add'),
    path('edit/<int:pk>/', RequirementUpdateView.as_view(), name='requirement_edit'),
    path('delete/<int:pk>/',RequirementDeleteView.as_view(),name='requirement_delete'),
    path('defect/add/<int:pk>/', RequirementDefectAddView.as_view(), name='requirement_defect_add'),
    path('defect/edit/<int:pk>/', RequirementDefectUpdateView.as_view(), name='requirement_defect_update'),
    path('detail/<int:pk>/', RequirementDetailView.as_view(), name='requirement_detail'),

]