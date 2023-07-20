from django.contrib import admin
from django.urls import path
from .views import *

urlpatterns = [

    path('list/', ContactListView.as_view(), name='list'),
    path('add/', ContactAddUpdateView.as_view(), name='add'),
    path('edit/<int:pk>/', ContactAddUpdateView.as_view(), name='edit'),
    path('delete/<int:pk>/',ContactDeleteView.as_view(),name='delete_contact')
]
