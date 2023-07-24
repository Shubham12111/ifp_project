from .views import *
from django.urls import path
from django.contrib.auth.decorators import login_required


urlpatterns = [
    path('list/', login_required(ToDoListAPIView.as_view()), name='todo_list'),
    path('add/', login_required(ToDoAddView.as_view()), name='todo_add'),  # URL for creating new todo (POST)
    path('edit/<int:pk>/', login_required(ToDoAddView.as_view()), name='edit_task'),
    path('view/<int:pk>/', login_required(ToDoAddView.as_view()), name='view_task'),
    
    
]
