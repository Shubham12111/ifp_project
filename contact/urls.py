
from django.urls import path
from .views import MessageListView,ContactListCreateView
from django.contrib import admin

urlpatterns = [

    path('contacts/', ContactListCreateView.as_view(), name='contact-list'), 
    path('contacts/create/', ContactListCreateView.as_view(), name='contact-create'),
    path('messages/', MessageListView.as_view(), name='messages'),

]
