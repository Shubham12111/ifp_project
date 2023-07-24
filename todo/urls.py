from .views import *
from django.urls import path
from django.contrib.auth.decorators import login_required


urlpatterns = [
    path('list/', login_required(ToDoView.as_view()), name='todo_list'),
    path('add/', login_required(ToDoAddView.as_view()), name='todo_add'),
    path('edit/<int:pk>/', login_required(ToDoAddView.as_view()), name='edit_task'),
    
]
