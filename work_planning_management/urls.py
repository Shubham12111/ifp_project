# your_app_name/urls.py
from django.urls import path
from . import views
from .views import *
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

from django.contrib.auth.decorators import login_required
from .site_pack_views import DocumentListView,DocumentAddView,DocumentDeleteView,download_document,SitepackJobListView,DocumentJobDeleteView

from .rlo_views import *





urlpatterns = [
    path('approved_quotation/', ApprovedQuotationCustomerListView.as_view(), name='approved_quotation_view'),
    path('customer/<int:customer_id>/approved-quotation/', ApprovedQuotationListView.as_view(), name='approved_quotation_list'),


    path('job-customers/', JobCustomerListView.as_view(), name='job_customers_list'),
    
    path('customer/<int:customer_id>/jobs/', JobsListView.as_view(), name='jobs_list'),
    # path('customer/<int:customer_id>/jobs/job/<int:job_id>/delete/', views.JobDeleteView.as_view(), name='job_delete'),
    path('customer/<int:customer_id>/jobs/job/<int:job_id>/details/', JobDetailView.as_view(), name='job_detail'),
    path('customer/<int:customer_id>/jobs/<int:job_id>/site-packs/', JobSitePacksDetailView.as_view(), name='job_site_packs_detail'),
    path('customer/<int:customer_id>/jobs/<int:job_id>/site-packs/<int:site_pack_id>/download/', JobSitePacksDownloadView.as_view(), name='job_site_packs_download'),
    path('customer/<int:customer_id>/jobs/<int:job_id>/site-packs/<int:site_pack_id>/delete/', JobSitePacksDeleteView.as_view(), name='job_site_packs_delete'),
    path('customer/<int:customer_id>/jobs/<int:job_id>/rlo/', JobRLODetailView.as_view(), name='job_rlo_detail'),
    path('customer/<int:customer_id>/jobs/<int:job_id>/rlo/add/', JobRLOAddView.as_view(),name='job_rlo_add'),
    path('customer/<int:customer_id>/jobs/<int:job_id>/rlo/<int:rlo_id>/delete/', JobRLODeleteView.as_view(),name='job_rlo_delete'),
    # path('customer/<int:customer_id>/jobs/<int:job_id>/rlo/<int:rlo_id>/download/', JobRLODownloadView.as_view(),name='job_rlo_download'),
    path('customer/<int:customer_id>/jobs/<int:job_id>/rlo/<int:rlo_id>/approve/', JobRLOApproveView.as_view(),name='job_rlo_approve'),
    path('customer/<int:customer_id>/jobs/<int:job_id>/rlo/<int:rlo_id>/reject/', JobRLORejectView.as_view(),name='job_rlo_reject'),
    path('customer/<int:customer_id>/jobs/<int:job_id>/mark-as-complete/', MarkAsCompleteJobView.as_view(), name='mark_as_complete'),
    path('customer/<int:customer_id>/jobs/<int:job_id>/start-job/', StartJobView.as_view(), name='start_job'), 
    path('customer/<int:customer_id>/jobs/<int:job_id>/po/', JobPODetailView.as_view(), name='job_po_detail'),



    # stw
    path('stw_customers/', STWCustomerListView.as_view(), name='stw_customers_list'),
    path('customer/<int:customer_id>/stw/', STWRequirementListView.as_view(), name='customer_stw_list'),
    path('customer/<int:customer_id>/stw/<int:pk>/view/', STWDetailView.as_view(), name='customer_stw_view'),
    path('customer/<int:customer_id>/stw/add/', STWRequirementAddView.as_view(), name='customer_stw_add'),
    path('customer/<int:customer_id>/stw/<int:pk>/edit/', STWRequirementUpdateView.as_view(), name='customer_stw_edit'),
    path('customer/<int:customer_id>/stw/<int:pk>/delete/',STWRequirementDeleteView.as_view(),name='customer_stw_delete'),
    path('delete/document/<int:stw_id>/<int:document_id>/', login_required(STWRemoveDocumentView.as_view()), name='remove_stw_document'),
    path('customer/<int:customer_id>/convert-stw-to-fra/<int:pk>/', ConvertToFRAView.as_view(), name='convert_to_fra'),


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
    path('members/delete/<int:pk>/', MemberDeleteView.as_view(), name='member_delete'),
    path('members/details/<int:pk>/', MemberDetailView.as_view(), name='member_details'),



    # Teams URLs
    path('teams/', TeamsListView.as_view(), name='teams_list'),
    path('teams/add/', TeamAddView.as_view(), name='team_add'),
    path('teams/edit/<int:team_id>/', views.TeamEditView.as_view(), name='team_edit'),
    path('teams/delete/<int:pk>/', views.TeamDeleteView.as_view(), name='team_delete'),
    path('teams/view/<int:pk>/', views.TeamDetailView.as_view(), name='team_detail'),



    # add job for stw
    path('stw_job/add/<int:stw_id>/', AddJobView.as_view(), name='stw_job'),
    path('stw/customer/<int:customer_id>/job_assign/', AssignJobView.as_view(), name='job_assign_stw'),

    # calendar urls
    path('member_calendar/', views.index, name='member_calendar'), 
    path('all_events/', views.all_events, name='all_events'), 
    path('add_event/', views.add_event, name='add_event'), 
    path('event_add/',EventAddView.as_view() , name='event_add'),
    path('event_edit/<int:event_id>/',EventUpdateView.as_view() , name='event_edit'),
    path('event_view/<int:event_id>/',EventdetailView.as_view() , name='event_view'),
    # path('remove/', views.remove, name='remove'),
    path('get_event_details/<int:event_id>/', views.get_event_details, name='get_event_details'),
    # path('stw/job_schedule/',AssignscheduleView.as_view(),name='job_schedule'),


    # RLO views:-
    path('RLO/list/', RLOListView.as_view(), name='rlo_list'),
    path('RLO/add/',RLOAddView.as_view(),name='rlo_add'),
    path('RLO/delete/<int:pk>/',RLODeleteView.as_view(),name='rlo_delete'),
    path('RLO/view/<int:pk>/', RLOpdfView.as_view(), name='rlo_detail'),
    path('RLO/get_template_content/', get_template_content, name='get_template_content'),
    path('rlo/<int:rlo_id>/reject/', RejectRLOView.as_view(), name='rlo_reject'),
    path('rlo/<int:rlo_id>/approve/', ApproveRLOView.as_view(), name='rlo_approve'),


    # sitepack 
    path('sitepack/document/list/', DocumentListView.as_view(), name='sitepack_document_list'),
    path('sitepack/document/add/',DocumentAddView.as_view(),name="document_add"),
    path('sitepack/document/delete/<int:pk>/',DocumentDeleteView.as_view(),name="document_delete"),
    path('sitepack/document_download/<int:asset_id>/', download_document, name='download_document'),
    path('sitepack/job/list/', SitepackJobListView.as_view(), name='sitepack_job_list'),
    # path('sitepack/job_document/add/', DocumentSelectView.as_view(), name='job_document_add'),
    path('sitepack/job_document/delete/<int:pk>/',DocumentJobDeleteView.as_view(),name="job_document_delete"),


    path('assigned-jobs/list/', retriveMembersAssignedJobs, name='list_assigned_jobs_of_members'),

]
