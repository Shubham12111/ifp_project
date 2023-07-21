from django.contrib import admin
from django.urls import path
from .views import *

urlpatterns = [
    path('list/', ToDoListView.as_view(), name='todo_list'),
   
    
]
