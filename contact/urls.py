from django.contrib import admin
from django.urls import path
from django.contrib.auth.decorators import login_required

from .views import *



urlpatterns = [

    path('list/', login_required(ContactListView.as_view()), name='contact_list'),
    path('add/', login_required(ContactAddUpdateView.as_view()), name='contact_add'),
    path('edit/<int:pk>/', login_required(ContactAddUpdateView.as_view()), name='contact_edit'),
    path('delete/<int:pk>/',login_required(ContactDeleteView.as_view()),name='delete_contact'),
    path('conversation/<int:pk>/', login_required(ConversationListView.as_view()), name='contact_conversation'),

]
