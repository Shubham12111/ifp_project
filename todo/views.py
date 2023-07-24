from django.http import JsonResponse
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.renderers import TemplateHTMLRenderer,JSONRenderer
from infinity_fire_solutions.response_schemas import create_api_response, render_html_response
from .models import *
from .serializers import *
from django.contrib import messages 
from django.shortcuts import redirect
from django.urls import reverse
from django.shortcuts import get_object_or_404
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import BasePermission,IsAuthenticated

from rest_framework.exceptions import PermissionDenied
from rest_framework import filters
from django.apps import apps
from django.contrib.auth.models import Permission


class CanReadPermission(BasePermission):
    READ_PERMISSIONS = {
        'view': 'view_{}',
    }

    def has_permission(self, request, view):
        app_name = view.get_app_name()

        for group in request.user.groups.all():
            for operation, codename in self.READ_PERMISSIONS.items():
                required_permission = codename.format(app_name)
                try:
                    permission = Permission.objects.get(codename=required_permission, content_type__app_label=app_name)
                    if permission in group.permissions.all():
                        return True
                except Permission.DoesNotExist:
                    continue

        return PermissionDenied()

class CanWritePermission(BasePermission):
    WRITE_PERMISSIONS = {
        'add': 'add_{}',
        'change': 'change_{}',
        'delete': 'delete_{}',
    }

    def has_permission(self, request, view):
        app_name = view.get_app_name()

        for group in request.user.groups.all():
            for operation, codename in self.WRITE_PERMISSIONS.items():
                required_permission = codename.format(app_name)
                try:
                    permission = Permission.objects.get(codename=required_permission, content_type__app_label=app_name)
                    if permission in group.permissions.all():
                        return True
                except Permission.DoesNotExist:
                    continue

        return False
    
class ToDoListAPIView(generics.ListAPIView):
    permission_classes = [CanReadPermission,IsAuthenticated]
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    ordering_fields = ['created_at']  # Specify fields you want to allow ordering on
    search_fields = ['title', 'description']  # Specify fields you want to allow searching on
    template_name = 'todo_list.html'
    
    def get_app_name(self):
        return apps.get_containing_app_config(self.__module__).name
    
    def get_queryset(self):
        queryset = Todo.objects.all()
        user_id = self.request.user.id

        # Add filtering based on user ID
        queryset = queryset.filter(user_id=user_id)

        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        # Filter the queryset based on ordering and searching
        queryset = self.filter_queryset(queryset)

        if request.accepted_renderer.format == 'html':
            # If the client accepts HTML, render the template
            context = {'todo_list': queryset}
            return render_html_response(context,self.template_name)
        else:
            serializer = self.serializer_class(queryset, many=True)
            return create_api_response(status_code=status.HTTP_200_OK,
                                       message="Data Retrieved successfully",
                                       data=serializer)
    

        
class ToDoAddView(generics.CreateAPIView):
    permission_classes = [CanWritePermission,IsAuthenticated]
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'todo_add.html'
    serializer_class = TodoAddSerializer

    def get_app_name(self):
        return apps.get_containing_app_config(self.__module__).name
    
    def get_queryset(self):
        queryset = Todo.objects.filter(pk=self.kwargs.get('pk'))
        user_id = self.request.user.id

        # Add filtering based on user ID
        queryset = queryset.filter(user_id=user_id)

        return queryset
        
    def get(self, request, *args, **kwargs):
        instance = None
        pk = kwargs.get('pk')

        if pk:
            instance = self.get_queryset().get()
            serializer = self.serializer_class(instance=instance)
        else:
            # If no primary key is provided, it means we are adding a new contact
            serializer = self.serializer_class()

        if request.accepted_renderer.format == 'html':
            # If the client accepts HTML, render the template
            context = {'serializer':serializer, 'instance':instance}
            return render_html_response(context,self.template_name)
            
    
    def post(self, request, *args, **kwargs):
        data = request.data
        pk = kwargs.get('pk')
        if pk:
            # If a primary key is provided, it means we are updating an existing contact
            todo_data =  self.get_queryset().get()
            serializer = self.serializer_class(instance=todo_data, data=data)
        else:
            # If no primary key is provided, it means we are adding a new contact
            serializer = self.serializer_class(data=data)

        
        if serializer.is_valid():
            serializer.validated_data['user_id'] = request.user
            serializer.save()
            if request.accepted_renderer.format == 'html':
                # For HTML rendering, redirect to the list view after successful save
                if pk:
                    messages.success(request, "Task Updated: Your TODO has been updated successfully!")
                else:
                    messages.success(request, "Task Added: Your TODO has been saved successfully!")
                return redirect(reverse('todo_list'))
            else:
                # For other formats (e.g., JSON), return success response
                return Response({
                    "status_code": status.HTTP_200_OK,
                    "message": "Data retrieved successfully",
                    "data": serializer.data
                })
        else:
            # Render the HTML template with invalid serializer data
            context = {'serializer': serializer}
            return Response(context, template_name=self.template_name)
           


class ToDoRetrieveAPIView(generics.RetrieveAPIView):
    permission_classes = [CanReadPermission, IsAuthenticated]
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    ordering_fields = ['created_at']  # Specify fields you want to allow ordering on
    search_fields = ['title', 'description']  # Specify fields you want to allow searching on
    template_name = 'todo_view.html'
    serializer_class = CommentSerializer
    
    def get_app_name(self):
        return apps.get_containing_app_config(self.__module__).name
    
    def get_queryset(self):
        queryset = Todo.objects.filter(pk=self.kwargs.get('todo_id'),user_id = self.request.user.id)
        return queryset

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset().get()
        if request.accepted_renderer.format == 'html':
            # If the client accepts HTML, render the template
            comment_list = Comment.objects.filter(todo_id=queryset).order_by('-created_at')
            context = {'todo_data': queryset,
                       'serializer':self.serializer_class,
                       'comment_list':comment_list}
            return render_html_response(context,self.template_name)
       
    
    def post(self, request, *args, **kwargs):
        data = request.data
        if self.get_queryset().get():
            # If a primary key is provided, it means we are updating an existing contact
            todo_data =  self.get_queryset().get()
            serializer = self.serializer_class(data=data)
            if serializer.is_valid():
                serializer.validated_data['user_id'] = request.user
                serializer.validated_data['todo_id'] = todo_data
                serializer.save()
                if request.accepted_renderer.format == 'html':
                    # For HTML rendering, redirect to the list view after successful save
                
                    return redirect(reverse('todo_list'))
                else:
                    # For other formats (e.g., JSON), return success response
                    return Response({
                        "status_code": status.HTTP_200_OK,
                        "message": "Data retrieved successfully",
                        "data": serializer.data
                    })
            