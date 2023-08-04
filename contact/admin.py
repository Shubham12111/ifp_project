from django.contrib import admin
from .models import Contact, ContactType, ConversationType, Conversation

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ['id','first_name','last_name', 'email', 'phone_number', 'contact_type', 'job_title', 'company', 'address', 'town', 'county', 'post_code', 'country', 'created_at', 'updated_at']
    list_filter = ['contact_type']
    search_fields = ['name', 'email']

@admin.register(ContactType)
class ContactTypeAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']


@admin.register(ConversationType)
class ConversationTypeAdmin(admin.ModelAdmin):
    list_display = ['name','created_at', 'updated_at']
    list_filter = ['name']
    search_fields = ['name']


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ['title', 'conversation_type', 'contact_id','message','created_at', 'updated_at']
    list_filter = ['title','conversation_type']
    search_fields = ['title','conversation_type']