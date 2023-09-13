from django.contrib import admin
from .models import Module, Todo, Comment

# Register your models here.

class ModuleAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Module model.
    """
    list_display = ('name', 'created_at', 'updated_at')

class TodoAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Todo model.
    """
    list_display = ('title', 'user_id', 'module', 'status', 'priority', 'start_date', 'end_date', 'assigned_to', 'created_at', 'updated_at')
    search_fields = ('title', 'description', 'assigned_to__username')  # Add fields for searching

class CommentAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Comment model.
    """
    list_display = ('todo_id', 'user_id', 'comment', 'status', 'created_at', 'updated_at')

admin.site.register(Module, ModuleAdmin)
admin.site.register(Todo, TodoAdmin)
admin.site.register(Comment, CommentAdmin)
