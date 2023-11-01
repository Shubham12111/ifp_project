from django.contrib import admin
from django.urls import path
from django.contrib.auth.decorators import login_required
from .views import *
from .reports import *
from .sor_view import *
from .quotation_views import *

urlpatterns = [
    path('quantity_surveyor/add/<int:customer_id>/',RequirementQSAddView.as_view() , name='add_quantity_surveyor'),
    path('surveyor/add/<int:customer_id>/',RequirementSurveyorAddView.as_view() , name='add_surveyor'),

    path('customers/', RequirementCustomerListView.as_view(), name='customers_list'),
    path('customers/<int:customer_id>/list/', RequirementListView.as_view(), name='customer_requirement_list'),
    path('customers/<int:customer_id>/add/', RequirementAddView.as_view(), name='customer_requirement_add'),
    path('<int:customer_id>/view/<int:pk>/', RequirementDetailView.as_view(), name='customer_requirement_view'),
    path('<int:customer_id>/view/<int:pk>/', RequirementDetailView.as_view(), name='customer_requirement_view'),
    
    path('<int:customer_id>/view/selecetd_defects/<int:pk>/', get_selected_defect_data, name='get_selected_defect_data'),
    path('customers/<int:customer_id>/<int:requirement_id>/defect/detail/<int:defect_id>/', RequirementDefectDetailView.as_view(), name='customer_requirement_defect_detail'),

    
    
    
    path('customers/<int:customer_id>/edit/<int:pk>/', RequirementUpdateView.as_view(), name='customer_requirement_edit'),
    path('customers/<int:customer_id>/delete/<int:pk>/',RequirementDeleteView.as_view(),name='customer_requirement_delete'),
    path('delete/document/<int:requirement_id>/<int:document_id>/', login_required(RequirementRemoveDocumentView.as_view()), name='remove_requirement_document'),
    
    path('customers/<int:customer_id>/<int:requirement_id>/defects/', RequirementDefectView.as_view(), name='customer_requirement_defects'),
    path('customers/<int:customer_id>/defects/edit/<int:requirement_id>/<int:pk>/', RequirementDefectView.as_view(), name='customer_requirement_defect_update'),

    
    path('reports/<int:customer_id>/<int:requirement_id>/', RequirementReportsListView.as_view(), name='customer_requirement_reports'),
    path('report/view/<int:customer_id>/<int:requirement_id>/<int:pk>/', ReportView.as_view(), name='requirement_report_view'),
    path('report/edit/<int:customer_id>/<int:requirement_id>/<int:pk>/', ReportEdit.as_view(), name='requirement_report_edit'),


    path('report/delete/<int:customer_id>/<int:requirement_id>/<int:pk>/', ReportRemoveView.as_view(), name='requirement_report_delete'),

    
    path('defects/delete/<int:pk>/', RequirementDefectDeleteView.as_view(), name='requirement_defect_delete'),
    path('defects/delete/document/<int:defect_id>/<int:pk>/', login_required(RequirementDefectRemoveDocumentView.as_view()), name='remove_requirement_defect_document'),

    path('customers/sor/', SORCustomerListView.as_view(), name='sor_customers_list'),
    path('customer/sor/<int:customer_id>/list/', SORListView.as_view(), name='customer_sor_list'),
    path('customer/sor/<int:customer_id>/add/', SORAddView.as_view(), name='add_sor_customer'),
    
    path('customer/sor/<int:customer_id>/edit/<int:sor_id>/', SORUpdateView.as_view(), name='edit_sor_customer'),
    path('customer/sor/<int:sor_id>/view/', SORDetailView.as_view(), name='sor_customers_detail'),
    path('customer/sor/delete/<int:sor_id>/', SORDeleteView.as_view(), name='delete_sor'),
    # path('customer/sor/delete/document/<int:customer_id>/<int:sor_id>/<int:document_id>', SORRemoveImageView.as_view(), name='delete_sor_document'),


    
    
    path('quotation/', QuotationCustomerListView.as_view(), name='view_customer_list_quotation'),
    path('quotation/<int:customer_id>/report/', QuotationCustomerReportListView.as_view(), name='view_customer_fra_list_report'),

    path('quotation/add/<int:customer_id>/report/<int:report_id>/', QuotationAddView.as_view(), name='add_customer_estimation'),

    path('quotation/edit/<int:customer_id>/quotation/<int:quotation_id>/', QuotationAddView.as_view(), name='edit_customer_estimation'),

    path('quotation/list/<int:customer_id>/', CustomerQuotationListView.as_view(), name='view_customer_quotation_list'),

    path('quotation/view/<int:customer_id>/<int:quotation_id>/', CustomerQuotationView.as_view(), name='customer_quotation_view'),

    path('customers/sor/import_csv_sor/<int:customer_id>/', SORCSVView.as_view(), name='import_csv_sor'),
    path('customers/fra/import_csv/<int:customer_id>/', RequirementCSVView.as_view(), name='import_csv'),


]   