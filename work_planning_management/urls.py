# your_app_name/urls.py
from django.urls import path
from . import views
from .views import *
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

from django.contrib.auth.decorators import login_required
from .site_pack_views import DocumentListView,DocumentAddView,DocumentDeleteView,download_document,SitepackJobListView,DocumentJobDeleteView

from .rlo_views import *
from schedule.models import Calendar
from schedule.views import (
    FullCalendarView,CalendarView,CalendarByPeriodsView
)




urlpatterns = [
    path('approved_quotation/', ApprovedQuotationCustomerListView.as_view(), name='approved_quotation_view'),
    path('approved_list/<int:customer_id>/list/', ApprovedQuotationListView.as_view(), name='approved_quotation_list'),


    path('job_customers/', JobCustomerListView.as_view(), name='job_customers_list'),
    path('jobs/add/<int:qoute_id>/', QuoteJobView.as_view(), name='job_add'),
    path('jobs/<int:customer_id>/list/', JobsListView.as_view(), name='jobs_list'),
    path('job/<int:job_id>/delete/', views.JobDeleteView.as_view(), name='job_delete'),
    path('job/<int:job_id>/', JobDetailView.as_view(), name='job_detail'),



    # stw
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
    path('members/delete/<int:pk>/', MemberDeleteView.as_view(), name='member_delete'),


    # Teams URLs
    path('teams/', TeamsListView.as_view(), name='teams_list'),
    path('teams/add/', TeamAddView.as_view(), name='team_add'),
    path('teams/edit/<int:team_id>/', views.TeamEditView.as_view(), name='team_edit'),
    path('teams/delete/<int:pk>/', views.TeamDeleteView.as_view(), name='team_delete'),
    path('teams/view/<int:pk>/', views.TeamDetailView.as_view(), name='team_detail'),



    # add job for stw
    path('stw_job/add/<int:stw_id>/', AddJobView.as_view(), name='stw_job'),
    path('stw/job_assign/',AssignJobView.as_view(),name='job_assign_stw'),

    # calendar urls
    path('calendar/<str:calendar_slug>/', CalendarView.as_view(), name='calendar_home'),
    path('fullcalendar/<str:calendar_slug>/', FullCalendarView.as_view(), name='fullcalendar'),
    path("calendar/compact_month/<calendar_slug>/",CalendarByPeriodsView.as_view(template_name="schedule/calendar_compact_month.html"),
        name="compact_calendar",
        kwargs={"period": Month},
    ),
    path("calendar/month/<calendar_slug>/",CalendarByPeriodsView.as_view(template_name="schedule/calendar_month.html"),
         name="month_calendar",
        kwargs={"period": Month},
    ),
    path("calendar/year/<calendar_slug>",CalendarByPeriodsView.as_view(template_name="schedule/calendar_year.html"),
        name="year_calendar",
        kwargs={"period": Year},
    ),
    path("calendar/tri_month/<calendar_slug>",CalendarByPeriodsView.as_view(template_name="schedule/calendar_tri_month.html"),
        name="tri_month_calendar",
        kwargs={"period": Month},
    ),
    path("calendar/week/<calendar_slug>",CalendarByPeriodsView.as_view(template_name="schedule/calendar_week.html"),
        name="week_calendar",
        kwargs={"period": Week},
    ),
    path("calendar/daily/<calendar_slug>",CalendarByPeriodsView.as_view(template_name="schedule/calendar_day.html"),
        name="day_calendar",
        kwargs={"period": Day},
    ),
    path("calendar/<calendar_slug>",CalendarView.as_view(),name="calendar_home"),
    path('api/get_events/', views.get_events_api, name='get_events_api'),



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

]
