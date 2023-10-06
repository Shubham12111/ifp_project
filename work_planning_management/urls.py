# your_app_name/urls.py
from django.urls import path
from . import views
from .views import *
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

from .views import *
from django.urls import path




urlpatterns = [
    path('approved_list/', ApprovedQuotationListView.as_view(), name='approved_quotation_list'),
]
    path('stw/search/', STWSearchAPIView.as_view(), name='stw_search'),
    path('stw/list/', STWListAPIView.as_view(), name='stw_list'),
    path('stw/add/', STWAddAPIView.as_view(), name='stw_add'),
    path('stw/edit/<int:stw_id>', STWUpdateView.as_view(), name='stw_edit'),
    path('stw/delete/<int:stw_id>', STWDeleteView.as_view(), name='stw_delete'),
    path('stw/view/<int:stw_id>/', STWDetailView.as_view(), name='stw_view'),
    

   
]
