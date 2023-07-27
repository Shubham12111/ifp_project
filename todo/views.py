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
from infinity_fire_solutions.permission import *
from rest_framework import filters
from django.apps import apps
from django.http import HttpResponseRedirect
from django.db.models import Q
from authentication.models import *
from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied

class HasListDataPermission(BasePermission):
    def __init__(self, module_name):
        self.module_name = module_name

    def has_permission(self, request, view):
        user = request.user
        for role in user.roles.all():
            permission = UserRolePermission.objects.filter(role=role, module=self.module_name).first()
            if permission:
                if permission.can_list_data == "none":
                    raise PermissionDenied()
                else:
                    return permission.can_list_data.lower()
        
        # If no permission is found, return False (no "self" or "all" permission)
        return False
    
    
class ToDoListAPIView(CustomAuthenticationMixin,generics.ListAPIView):
    """
    API view to list TODO items.

    This view lists TODO items filtered based on the authenticated user's ID.
    It supports filtering based on fields and searching based on title and description.

    Filters:
        - Ordering by 'created_at' field is allowed.

    Searching:
        - Searching is allowed on 'title' and 'description' fields.

    Renderer:
        - Supports both HTML and JSON renderers.

    Template (for HTML renderer):
        - Uses the 'todo_list.html' template to render HTML output.

    Serializer:
        - Uses the TodoListSerializer to serialize the data.

    Authentication and Permissions:
        - Inherits authentication and permission handling from CustomAuthenticationMixin.
    """

    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    ordering_fields = ['created_at']  # Specify fields you want to allow ordering on
    search_fields = ['title', 'description']  # Specify fields you want to allow searching on
    template_name = 'todo_list.html'
    serializer_class = TodoListSerializer
    
    def get_permissions(self):
        """
        Get the list of permission classes to apply.

        Returns:
            list: List of permission classes.
        """
        # You can return multiple permission classes here if needed
        authenticated_user = self.handle_unauthenticated()
        
        if isinstance(authenticated_user, HttpResponseRedirect):
            # If the user is not authenticated and a redirect response is received
            # (for HTML renderer), return the redirect response as it is.
            return authenticated_user
        
        if not authenticated_user:
            raise AuthenticationFailed("Authentication credentials were not provided")
        
        
        module_name = self.get_model_name()
        return [HasListDataPermission(module_name=module_name.lower())]
    
    
    def get_model_name(self):
        return self.serializer_class.Meta.model.__name__
    
    def get_queryset(self):
        """
        Get the queryset for listing TODO items.

        Returns:
            QuerySet: A queryset of TODO items filtered based on the authenticated user's ID.
        """
        # Get the model class using the provided module_name string
        module_name = self.get_model_name()
        
        permission_instance = self.get_permissions()[0]
        print(permission_instance)
        if permission_instance:
            can_list_data_value = permission_instance.has_permission(self.request, None)
            queryset = get_generic_queryset(self.request, module_name, "todo", can_list_data_value)
            return queryset


    def list(self, request, *args, **kwargs):
        """
        List view for TODO items.
        """
        # Call the handle_unauthenticated method to handle unauthenticated access
        queryset = self.get_queryset()

        # Filter the queryset based on ordering and searching
        queryset = self.filter_queryset(queryset)

        if request.accepted_renderer.format == 'html':
            # If the client accepts HTML, render the template
            context = {'todo_list': queryset}
            return render_html_response(context, self.template_name)
        else:
            serializer = self.serializer_class(queryset, many=True)
            return create_api_response(
                status_code=status.HTTP_200_OK,
                message="Todo data Retrieved successfully",
                data=serializer.data
            )

class ToDoAddUpdateView(CustomAuthenticationMixin, generics.CreateAPIView):
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

        # Call the handle_unauthenticated method to handle unauthenticated access
        authenticated_user = self.handle_unauthenticated()

        if isinstance(authenticated_user, HttpResponseRedirect):
            # If the user is not authenticated and a redirect response is received
            # (for HTML renderer), return the redirect response as it is.
            return authenticated_user
        
        if not authenticated_user:
            raise AuthenticationFailed("Authentication credentials were not provided")

        request.user  = authenticated_user

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

            if pk:
                message = "Your TODO has been updated successfully!"
                status_code = status.HTTP_200_OK
            else:
                message = "Your TODO has been saved successfully!"
                status_code = status.HTTP_201_CREATED

            if request.accepted_renderer.format == 'html':
                # For HTML rendering, redirect to the list view after successful save
                
                messages.success(request, message)
                return redirect(reverse('todo_list'))
            else:
                # For other formats (e.g., JSON), return success response
                return create_api_response(
                    status_code,
                    f"{message}",
                    serializer.data
                )
        else:
            # Render the HTML template with invalid serializer data
            if request.accepted_renderer.format == 'html':
                context = {'serializer': serializer}
                return Response(context, template_name=self.template_name)
            else:
                # For JSON API response
                return create_api_response(
                    status.HTTP_400_BAD_REQUEST,
                    "Something went wrong!",
                    serializer.errors
                )

class ToDoDeleteView(CustomAuthenticationMixin, generics.DestroyAPIView):

    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    
    def get_queryset(self):
        user_id = self.request.user.id
        return Todo.objects.filter(pk=self.kwargs.get('pk'), user_id=user_id)

    def delete(self, request, *args, **kwargs):
        # Call the handle_unauthenticated method to handle unauthenticated access
        authenticated_user = self.handle_unauthenticated()

        if isinstance(authenticated_user, HttpResponseRedirect):
            # If the user is not authenticated and a redirect response is received
            # (for HTML renderer), return the redirect response as it is.
            return authenticated_user
        
        if not authenticated_user:
            raise AuthenticationFailed("Authentication credentials were not provided")

        request.user  = authenticated_user
        
        instance = self.get_queryset().first()
        if instance:
            instance.delete()

            return create_api_response(
                status.HTTP_200_OK,
                "Your TODO has been deleted successfully.",
            )
        else:
            return create_api_response(
                status.HTTP_404_NOT_FOUND,
                "TODO not found or you don't have permission to delete."
            )

class ToDoRetrieveAPIView(generics.RetrieveAPIView):
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