# your_app_name/urls.py
from django.urls import path
from . import views
from .views import *
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

from .views import *
from django.urls import path
from django.contrib.auth.decorators import login_required
from .site_pack_views import DocumentListView,DocumentAddView,DocumentDeleteView,DocumentView




urlpatterns = [
    path('approved_quotation/', ApprovedQuotationCustomerListView.as_view(), name='approved_quotation_view'),
    path('approved_list/<int:customer_id>/list/', ApprovedQuotationListView.as_view(), name='approved_quotation_list'),
    # path('stw/search/', STWSearchAPIView.as_view(), name='stw_search'),
    # path('stw/list/', STWListAPIView.as_view(), name='stw_list'),
    # path('stw/add/', STWAddAPIView.as_view(), name='stw_add'),
    # path('stw/edit/<int:stw_id>', STWUpdateView.as_view(), name='stw_edit'),
    # path('stw/delete/<int:stw_id>', STWDeleteView.as_view(), name='stw_delete'),
    # path('stw/view/<int:stw_id>/', STWDetailView.as_view(), name='stw_view'),

    path('jobs/add/<int:qoute_id>/', QuoteJobView.as_view(), name='job_add'),
    path('jobs/list/', JobsListView.as_view(), name='jobs_list'),

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


    # sitepack 
    path('sitepack/document/list/', DocumentListView.as_view(), name='sitepack_document_list'),
    path('sitepack/document/add/',DocumentAddView.as_view(),name="document_add"),
    path('sitepack/document/delete/<int:pk>/',DocumentDeleteView.as_view(),name="document_delete"),
    path('sitepack/document/view/<int:pk>/',DocumentView.as_view(),name="document_view")

]
