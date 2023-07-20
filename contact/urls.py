from django.contrib import admin
from django.urls import path
from .views import *

urlpatterns = [

    path('list/', ContactListView.as_view(), name='contact_list'),
    path('add/', ContactAddUpdateView.as_view(), name='contact_add'),
    path('edit/<int:pk>/', ContactAddUpdateView.as_view(), name='contact_edit'),
    path('delete/<int:pk>/',ContactDeleteView.as_view(),name='delete_contact'),
    path('messages/', MessageListView.as_view(), name='messages'),
]
