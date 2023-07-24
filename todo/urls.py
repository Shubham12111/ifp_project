from .views import *
from django.urls import path
from django.contrib.auth.decorators import login_required


urlpatterns = [
    path('list/', login_required(ToDoListAPIView.as_view()), name='todo_list'),
    path('add/', login_required(ToDoAddView.as_view()), name='todo_add'),  # URL for creating new todo (POST)
    path('edit/<int:pk>/', login_required(ToDoAddView.as_view()), name='todo_edit'),
    path('delete/<int:pk>/', login_required(ToDoDeleteView.as_view()), name='todo_delete'),
    path('view/<int:todo_id>/', login_required(ToDoRetrieveAPIView.as_view()), name='todo_view'), 
    path('view/comment/edit/<int:todo_id>/<int:comment_id>/', login_required(ToDoRetrieveAPIView.as_view()), name='edit_comment'),   
    path('view/comment/delete/<int:todo_id>/<int:comment_id>/', login_required(ToDoDeleteCommentView.as_view()), name='delete_comment'),   

]
