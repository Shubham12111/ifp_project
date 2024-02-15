from django.contrib import admin
from .models import Contact, ContactType, ConversationType, Conversation

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    """
    Admin class for Contact model.
    """
    list_display = ['id','first_name','last_name', 'email', 'phone_number', 'contact_type', 'job_title', 'company_name', 'address', 'town', 'county', 'post_code', 'country', 'created_at', 'updated_at']
    list_filter = ['contact_type'] # Filter options for 'contact_type'
    search_fields = ['name', 'email'] # Search options for 'first_name', 'last_name', and 'email'

@admin.register(ContactType)
class ContactTypeAdmin(admin.ModelAdmin):
    """
    Admin class for ContactType model.
    """
    list_display = ['name']  # Display 'name' field
    search_fields = ['name']   # Search options for 'name'


@admin.register(ConversationType)
class ConversationTypeAdmin(admin.ModelAdmin):
    """
    Admin class for ConversationType model.
    """
    list_display = ['name','created_at', 'updated_at'] # Display 'name', 'created_at', and 'updated_at' fields
    list_filter = ['name']   # Filter options for 'name'
    search_fields = ['name']    # Search options for 'name'


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    """
    Admin class for Conversation model.
    """
    list_display = ['title', 'conversation_type', 'contact_id','message','created_at', 'updated_at']  # Display these fields
    list_filter = ['title','conversation_type']    # Filter options for 'title' and 'conversation_type'
    search_fields = ['title','conversation_type']    # Search options for 'title' and 'conversation_type'