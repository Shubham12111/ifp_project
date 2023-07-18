from django.contrib import admin
from django.urls import path
from .views import ContactListCreateView


urlpatterns = [

    path('contacts/', ContactListCreateView.as_view(), name='contact-list'), 
    path('contacts/create/', ContactListCreateView.as_view(), name='contact-create'),
]
