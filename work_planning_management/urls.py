# your_app_name/urls.py
from django.urls import path
from . import views
from .views import *
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

from django.contrib.auth.decorators import login_required
from .rlo_views import *




urlpatterns = [
    path('approved_quotation/', ApprovedQuotationCustomerListView.as_view(), name='approved_quotation_view'),
    path('approved_list/<int:customer_id>/list/', ApprovedQuotationListView.as_view(), name='approved_quotation_list'),


    path('job_customers/', JobCustomerListView.as_view(), name='job_customers_list'),
    path('jobs/add/<int:qoute_id>/', QuoteJobView.as_view(), name='job_add'),
    path('jobs/list/', JobsListView.as_view(), name='jobs_list'),
    path('job/<int:job_id>/delete/', views.JobDeleteView.as_view(), name='job_delete'),
    path('job/<int:job_id>/', JobDetailView.as_view(), name='job_detail'),




    path('stw_customers/', STWCustomerListView.as_view(), name='stw_customers_list'),
    path('stw_customers/<int:customer_id>/list/', STWRequirementListView.as_view(), name='customer_stw_list'),
    path('stw_customers/<int:customer_id>/add/', STWRequirementAddView.as_view(), name='customer_stw_add'),
    path('stw_customers/<int:customer_id>/edit/<int:pk>/', STWRequirementUpdateView.as_view(), name='customer_stw_edit'),
    path('stw_customers/<int:customer_id>/delete/<int:pk>/',STWRequirementDeleteView.as_view(),name='customer_stw_delete'),
    path('delete/document/<int:stw_id>/<int:document_id>/', login_required(STWRemoveDocumentView.as_view()), name='remove_stw_document'),
    path('<int:customer_id>/view/<int:pk>/', STWDetailView.as_view(), name='customer_stw_view'),

    # defects
    path('stw_customers/<int:customer_id>/<int:stw_id>/defects/', STWDefectView.as_view(), name='customer_stw_defects'),
    path('stw_customers/<int:customer_id>/defects/edit/<int:stw_id>/<int:pk>/', STWDefectView.as_view(), name='customer_stw_defect_update'),
    path('stw_defects/delete/<int:pk>/', STWDefectDeleteView.as_view(), name='stw_defect_delete'),
    path('stw_defects/delete/document/<int:defect_id>/<int:pk>/', login_required(STWDefectRemoveDocumentView.as_view()), name='remove_stw_defect_document'),
    path('stw_customers/<int:customer_id>/<int:stw_id>/defect/detail/<int:defect_id>/', STWDefectDetailView.as_view(), name='customer_stw_defect_detail'),

    # sor 
    path('sor/list/', STWDefectView.as_view(), name='stw_sor_list'),
    path('defect/<int:defect_id>/add_sor/<int:customer_id>/', STWSORAddView.as_view(), name='add_sor'),
    path('defect/<int:defect_id>/add_sor/<int:customer_id>/', STWSORAddView.as_view(), name='add_sor'),
    path('defect/<int:defect_id>/add_sor/<int:customer_id>/', STWSORAddView.as_view(), name='add_sor'),

    # Members URLs
    path('members/', MembersListView.as_view(), name='members_list'),
    path('members/form/', MemberFormView.as_view(), name='member_form'),
    path('members/add/<int:qoute_id>/', MemberFormView.as_view(), name='members_add'),
    path('members/edit/<int:pk>/', MemberEditView.as_view(), name='member_edit'),
    path('members/delete/<int:member_id>/', MemberDeleteView.as_view(), name='member_delete'),
    path('members/<int:member_id>/view/<int:pk>/', views.MemberDetailView.as_view(), name='member_detail'),


    # Teams URLs
    path('teams/', TeamsListView.as_view(), name='teams_list'),
    path('teams/create/', TeamAddView.as_view(), name='team_create'),
    path('team_edit/<int:team_id>/', views.TeamEditView.as_view(), name='team_edit'),
    path('teams/<int:pk>/', views.TeamDeleteView.as_view(), name='team_delete'),
    path('teams/<int:pk>/', views.TeamDetailView.as_view(), name='team_detail'),


    # RLO views:-
    path('RLO/list/', RLOListView.as_view(), name='rlo_list'),
    path('RLO/add/',RLOAddView.as_view(),name='rlo_add'),
    path('RLO/delete/<int:pk>/',RLODeleteView.as_view(),name='rlo_delete'),
    path('RLO/view/<int:pk>/', RLOpdfView.as_view(), name='rlo_detail'),
    path('RLO/get_template_content/', get_template_content, name='get_template_content'),
]
