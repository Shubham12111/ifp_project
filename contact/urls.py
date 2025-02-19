from django.contrib import admin
from django.urls import path
from django.contrib.auth.decorators import login_required

from .views import *



urlpatterns = [
    path('list/', ContactListView.as_view(), name='contact_list'),
    path('add/', ContactAddView.as_view(), name='contact_add'),
    path('edit/<int:pk>/', ContactUpdateView.as_view(), name='contact_edit'),
    path('delete/<int:pk>/',ContactDeleteView.as_view(),name='delete_contact'),
    path('conversation/<int:contact_id>/', ConversationView.as_view(), name='contact_conversation'),
    path('conversation/edit/<int:contact_id>/<int:conversation_id>', login_required(ConversationView.as_view()), name='edit_conversation'),
    path('conversation/delete/<int:contact_id>/<int:conversation_id>', login_required(ConversationCommentView.as_view()), name='delete_conversation'),
    path('conversation/delete/document/<int:contact_id>/<int:conversation_id>', login_required(ConversationRemoveDocumentView.as_view()), name='document_conversation'),
    path('autocomplete_contact/', ContacttypeAutocomplete.as_view(), name='contact-autocomplete'),
    path('export_csv/', ExportCSVView.as_view(), name='export_csv'),
    path('sub-contractor/serach/', SubContractorSearchAPIView.as_view(), name='sub_contractor_search'),

]
