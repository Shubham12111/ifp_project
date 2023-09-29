from .views import *
from django.urls import path



urlpatterns = [
    path('stw/search/', STWSearchAPIView.as_view(), name='stw_search'),
    path('stw/list/', STWListAPIView.as_view(), name='stw_list'),
    path('stw/add/', STWAddAPIView.as_view(), name='stw_add'),
    path('stw/edit/<int:stw_id>', STWUpdateView.as_view(), name='stw_edit'),
    path('stw/delete/<int:stw_id>', STWDeleteView.as_view(), name='stw_delete'),
    path('stw/view/<int:stw_id>/', STWDetailView.as_view(), name='stw_view'),
    

   
]