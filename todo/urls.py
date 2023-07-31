from .views import *
from django.urls import path
from django.contrib.auth.decorators import login_required


urlpatterns = [
    path('list/', ToDoListAPIView.as_view(), name='todo_list'),
    path('add/', ToDoAddUpdateView.as_view(), name='todo_add'),
    path('edit/<int:pk>/', ToDoAddUpdateView.as_view(), name='todo_edit'),
    path('delete/<int:pk>/', ToDoDeleteView.as_view(), name='todo_delete'),
    path('view/<int:todo_id>/', login_required(ToDoRetrieveAPIView.as_view()), name='todo_view'), 
    path('view/comment/edit/<int:todo_id>/<int:comment_id>/', login_required(ToDoRetrieveAPIView.as_view()), name='edit_comment'),   
    path('view/comment/delete/<int:todo_id>/<int:comment_id>/', login_required(ToDoDeleteCommentView.as_view()), name='delete_comment'),   

]
