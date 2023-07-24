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
from django.db.models import Q


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
        user_id = self.request.user

        queryset = Todo.objects.filter( Q(user_id=user_id) | Q(assigned_to=user_id)
        ).distinct().order_by('-created_at')
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
            serializer = self.serializer_class(instance=instance,context={'request': request})
        else:
            # If no primary key is provided, it means we are adding a new contact
            serializer = self.serializer_class(context={'request': request})

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
            serializer = self.serializer_class(instance=todo_data, data=data,context={'request': request})
        else:
            # If no primary key is provided, it means we are adding a new contact
            serializer = self.serializer_class(data=data,context={'request': request})

        
        if serializer.is_valid():
            serializer.validated_data['user_id'] = request.user
            serializer.save()
            if request.accepted_renderer.format == 'html':
                # For HTML rendering, redirect to the list view after successful save
                if pk:
                    messages.success(request, "Your TODO has been updated successfully!")
                else:
                    messages.success(request, "Your TODO has been saved successfully!")
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
           

class ToDoDeleteView(generics.DestroyAPIView):
    permission_classes = [CanWritePermission, IsAuthenticated]

    def get_app_name(self):
        return apps.get_containing_app_config(self.__module__).name

    def get_queryset(self):
        user_id = self.request.user.id
        return Todo.objects.filter(pk=self.kwargs.get('pk'), user_id=user_id)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_queryset().first()
        if instance:
            self.perform_destroy(instance)
            return Response(
                {"message": "Your TODO has been deleted successfully."},
                status=status.HTTP_204_NO_CONTENT
            )
        else:
            return Response(
                {"message": "TODO not found or you don't have permission to delete."},
                status=status.HTTP_404_NOT_FOUND
            )

class ToDoRetrieveAPIView(generics.RetrieveAPIView):
    permission_classes = [CanReadPermission, IsAuthenticated]
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    serializer_class = CommentSerializer
    template_name = 'todo_view.html'
    
    def get_app_name(self):
        return apps.get_containing_app_config(self.__module__).name
    
    def get_queryset(self):
        user = self.request.user
        todo_id = self.kwargs.get('todo_id')

        # Build the queryset with OR condition
        queryset = Todo.objects.filter(
            Q(pk=todo_id, user_id=user.id) | Q(assigned_to=user, pk=todo_id)
        )
        return queryset

    def get_comment_queryset(self):
        todo_queryset = self.get_queryset()
        queryset = Comment.objects.filter(todo_id=todo_queryset.get()).order_by('-created_at')
        return queryset

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset().get()
        if request.accepted_renderer.format == 'html':
            # If the client accepts HTML, render the template
            comment_id = self.kwargs.get('comment_id')
            if comment_id:
                comment_instance =  Comment.objects.filter(todo_id=queryset,pk=comment_id, user_id=request.user).get()
                serializer = self.serializer_class(instance=comment_instance)
            else:
                serializer =  self.serializer_class()
            
            comment_list = self.get_comment_queryset()
            context = {'todo_data': queryset,
                       'serializer':serializer,
                       'comment_list':comment_list}
            return render_html_response(context,self.template_name)
       
    
    def post(self, request, *args, **kwargs):
        data = request.data
        todo_data =  self.get_queryset().get()
        if todo_data:
            # If a primary key is provided, it means we are updating an existing contact
            comment_id = self.kwargs.get('comment_id')
            if comment_id:
                comment_instance =  Comment.objects.filter(todo_id=todo_data,pk=comment_id,user_id=request.user).first()
                serializer = self.serializer_class(data=data, instance=comment_instance)
            else:
                serializer = self.serializer_class(data=data)
            
            if serializer.is_valid():
                serializer.validated_data['user_id'] = request.user
                serializer.validated_data['todo_id'] = todo_data
                serializer.save()
                todo_data.status = serializer.data.get('status') 
                todo_data.save()
                if request.accepted_renderer.format == 'html':
                    # For HTML rendering, redirect to the list view after successful savemessages.success(request, "Task Added: Your TODO and comments have been saved successfully!")
                    messages.success(request, "Your comments have been saved successfully!")
                    return redirect(reverse('todo_view', kwargs={'todo_id': kwargs['todo_id']}))

                else:
                    # For other formats (e.g., JSON), return success response
                    return Response({
                        "status_code": status.HTTP_200_OK,
                        "message": "Data retrieved successfully",
                        "data": serializer.data
                    })
            else:
                # Render the HTML template with invalid serializer data
                context = {'todo_data': todo_data,
                       'serializer':serializer,
                       'comment_list':self.get_comment_queryset()}
                return Response(context, template_name=self.template_name)

class ToDoDeleteCommentView(generics.DestroyAPIView):
    def get_app_name(self):
        return apps.get_containing_app_config(self.__module__).name
    
    def get_queryset(self):
        user_id = self.request.user.id
        return Todo.objects.filter(pk=self.kwargs.get('todo_id'), user_id=user_id)
    
    def destroy(self, request, *args, **kwargs):
        todo = self.get_queryset()
        comment_id = kwargs.get('comment_id')
        if comment_id:
            comment = Comment.objects.filter(todo_id=todo.get(), user_id=request.user , pk=comment_id)
            comment.delete()
            return Response(
                {"message": "Your comment has been deleted successfully."},
                status=status.HTTP_204_NO_CONTENT
            )
        else:
            return Response(
                {"message": "Comment not found or you don't have permission to delete."},
                status=status.HTTP_404_NOT_FOUND
            )