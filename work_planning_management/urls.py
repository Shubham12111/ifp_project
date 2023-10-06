# your_app_name/urls.py
from django.urls import path
from . import views
from .views import *
from drf_yasg.views import get_schema_view
from drf_yasg import openapi



urlpatterns = [
    path('approved_list/', ApprovedQuotationListView.as_view(), name='approved_quotation_list'),
]
