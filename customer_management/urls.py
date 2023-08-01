from django.contrib import admin
from django.urls import path
from django.contrib.auth.decorators import login_required

from .views import *



urlpatterns = [
    path('', CustomerView.as_view(), name='customer'),
    path('list/', CustomerListView.as_view(), name='contact_list'),
]
