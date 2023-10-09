from .views import *
from django.urls import path
from django.contrib.auth.decorators import login_required



urlpatterns = [

    path('stw/search/', STWSearchAPIView.as_view(), name='stw_search'),
    path('stw/list/', STWListAPIView.as_view(), name='stw_list'),
    path('stw/add/', STWAddAPIView.as_view(), name='stw_add'),
    path('stw/edit/<int:stw_id>', STWUpdateView.as_view(), name='stw_edit'),
    path('stw/delete/<int:stw_id>', STWDeleteView.as_view(), name='stw_delete'),
    path('stw/view/<int:stw_id>/', STWDetailView.as_view(), name='stw_view'),
    path('jobs/list/', JobListView.as_view(), name='job_list'),
    path('jobs/add/', JobAddView.as_view(), name='job_add'),
    path('jobs/<int:pk>/update/', JobUpdateView.as_view(), name='job_update'),
    path('jobs/<int:pk>/delete/', JobDeleteView.as_view(), name='job_delete'),
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
    path('defect/<int:defect_id>/add_sor/<int:customer_id>/', STWSORAddView.as_view(), name='add_sor')

    

   
]