from django.contrib import admin
from django.urls import path
from .views import *

urlpatterns = [

    path('list/', ContactListView.as_view(), name='list'),
    path('add/', ContactAddUpdateView.as_view(), name='add'),
    path('edit/<int:pk>/', ContactAddUpdateView.as_view(), name='edit'),
    path('contacts/', ContactListCreateView.as_view(), name='contact-list'), 
    path('contacts/create/', ContactListCreateView.as_view(), name='contact-create'),
    path('messages/', MessageListView.as_view(), name='messages'),
]
