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
from rest_framework.decorators import permission_classes


class ToDoListAPIView(CustomAuthenticationMixin,generics.ListAPIView):
    """
    API view to list TODO items.
    """
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    ordering_fields = ['created_at']  # Specify fields you want to allow ordering on
    search_fields = ['title', 'description']  # Specify fields you want to allow searching on
    template_name = 'todo_list.html'
    serializer_class = TodoListSerializer
    
    def get_model_name(self):
        return self.serializer_class.Meta.model.__name__
    
    def get_permissions(self):
        """
        Get the list of permission classes to apply.

        Returns:
            list: List of permission classes.
        """
        try:
            authenticated_user = self.handle_unauthenticated()

            if isinstance(authenticated_user, HttpResponseRedirect):
                return authenticated_user

            if not authenticated_user:
                raise AuthenticationFailed("Authentication credentials were not provided")

            self.request.user = authenticated_user
            module_name = self.get_model_name()
            return [HasListDataPermission(module_name=module_name.lower())]
        except Exception as e:
            print(e)
    
    def list(self, request, *args, **kwargs):
        """
        List view for TODO items.

        Args:
            request (Request): The request object.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Response: The response containing the list of TODO items.
        """
        user_id = self.request.user
        # Get the first permission instance from the list of permission classes
        permission_instance = self.get_permissions()[0]

        # Get the data access value (either "self" or "all") from the permission instance
        data_access_value = permission_instance.has_permission(self.request, None)

        # Define a mapping of data access values to corresponding filters
        filter_mapping = {
            "self": Q(user_id=user_id) | Q(assigned_to=user_id),
            "all": Q(),  # An empty Q() object returns all data
        }

        # Get the appropriate filter from the mapping based on the data access value,
        # or use an empty Q() object if the value is not in the mapping
        queryset = Todo.objects.filter(filter_mapping.get(data_access_value, Q())).distinct().order_by('-created_at')
        
        queryset = self.filter_queryset(queryset)

        if request.accepted_renderer.format == 'html':
            # If the client accepts HTML, render the template
            context = {'todo_list': queryset}
            return render_html_response(context, self.template_name)
        else:
            # If the client accepts other formats, serialize the data and return an API response
            serializer = self.serializer_class(queryset, many=True)
            return create_api_response(
                status_code=status.HTTP_200_OK,
                message="Todo data retrieved successfully",
                data=serializer.data
            )
        
class ToDoAddView(CustomAuthenticationMixin, generics.CreateAPIView):

    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'todo_add.html'
    serializer_class = TodoAddSerializer

    def get_model_name(self):
        return self.serializer_class.Meta.model.__name__
    

    def get_permissions(self):
        """
        Get the list of permission classes to apply.

        Returns:
            list: List of permission classes.
        """
        # You can return multiple permission classes here if needed
        try:
            authenticated_user = self.handle_unauthenticated()
            
            if isinstance(authenticated_user, HttpResponseRedirect):
                # If the user is not authenticated and a redirect response is received
                # (for HTML renderer), return the redirect response as it is.
                return authenticated_user
            
            if not authenticated_user:
                raise AuthenticationFailed("Authentication credentials were not provided")
            
            self.request.user  = authenticated_user
            module_name = self.get_model_name()
            return [HasCreateDataPermission(module_name=module_name.lower())]
        
        except Exception as e:
            print(e)
        
    def get(self, request, *args, **kwargs):
        serializer = self.serializer_class(context={'request': request})

        if request.accepted_renderer.format == 'html':
            # If the client accepts HTML, render the template
            context = {'serializer':serializer}
            return render_html_response(context,self.template_name)
     
    def post(self, request, *args, **kwargs):

        serializer = self.serializer_class(data=request.data,context={'request': request})
        if serializer.is_valid():
            serializer.validated_data['user_id'] = request.user
            serializer.save()
            message = "Your TODO has been saved successfully!"
            status_code = status.HTTP_201_CREATED

            if request.accepted_renderer.format == 'html':
                # For HTML rendering, redirect to the list view after successful save
                
                messages.success(request, message)
                return redirect(reverse('todo_list'))
            else:
                # For other formats (e.g., JSON), return success response
                return create_api_response(status_code, f"{message}",serializer.data)
        else:
            # Render the HTML template with invalid serializer data
            if request.accepted_renderer.format == 'html':
                context = {'serializer': serializer}
                return Response(context, template_name=self.template_name)
            else:
                # For JSON API response
                return create_api_response(status.HTTP_400_BAD_REQUEST,"Something went wrong!",serializer.errors)


class ToDoUpdateView(CustomAuthenticationMixin, generics.UpdateAPIView):
    
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'todo_add.html'
    serializer_class = TodoAddSerializer

    def get_model_name(self):
        return self.serializer_class.Meta.model.__name__
    

    def get_permissions(self):
        """
        Get the list of permission classes to apply.

        Returns:
            list: List of permission classes.
        """
        # You can return multiple permission classes here if needed
        try:
            authenticated_user = self.handle_unauthenticated()
            
            if isinstance(authenticated_user, HttpResponseRedirect):
                # If the user is not authenticated and a redirect response is received
                # (for HTML renderer), return the redirect response as it is.
                return authenticated_user
            
            if not authenticated_user:
                raise AuthenticationFailed("Authentication credentials were not provided")
            self.request.user  = authenticated_user
            module_name = self.get_model_name()
            return [HasUpdateDataPermission(module_name=module_name.lower())]
        
        except Exception as e:
            print(e)

    def get_queryset(self):
        """
        Get the queryset for listing TODO items.

        Returns:
            QuerySet: A queryset of TODO items filtered based on the authenticated user's ID.
        """
        # Get the model class using the provided module_name string
        user_id = self.request.user
        
        permission_instance = self.get_permissions()[0]

        # Get the data access value (either "self" or "all") from the permission instance
        data_access_value = permission_instance.has_permission(self.request, None)

        # Define a mapping of data access values to corresponding filters
        filter_mapping = {
            "self": Q(user_id=user_id) | Q(assigned_to=user_id),
            "all": Q(),  # An empty Q() object returns all data
        }

        # Get the appropriate filter from the mapping based on the data access value,
        # or use an empty Q() object if the value is not in the mapping
        queryset = Todo.objects.filter(filter_mapping.get(data_access_value, Q())).distinct().order_by('-created_at')
        queryset = queryset.filter(pk=self.kwargs.get('pk')).first()
        
        return queryset

    
    def get(self, request, *args, **kwargs):
        # This method handles GET requests for updating an existing ToDo object.
        if request.accepted_renderer.format == 'html':
            instance = self.get_queryset()
            if instance:
                serializer = self.serializer_class(instance=instance, context={'request': request})
                context = {'serializer': serializer, 'instance': instance}
                return render_html_response(context, self.template_name)
            else:
                messages.error(request, "You are not authorized to perform this action")
                return redirect(reverse('todo_list'))
    
    def put(self, request, *args, **kwargs):
        
        data = request.data
        
        instance = self.get_queryset()
        if instance:
            serializer = self.serializer_class(instance=instance, data=data, context={'request': request})
            if serializer.is_valid():
                serializer.validated_data['user_id'] = request.user
                serializer.save()

                message = "Your TODO has been updated successfully!"
                status_code = status.HTTP_200_OK

                if request.accepted_renderer.format == 'html':
                    messages.success(request, message)
                    return redirect(reverse('todo_list'))
                else:
                    return create_api_response(status_code, f"{message}", serializer.data)
            else:
                if request.accepted_renderer.format == 'html':
                    context = {'serializer': serializer}
                    return Response(context, template_name=self.template_name)
                else:
                    return create_api_response(status.HTTP_400_BAD_REQUEST, "Something went wrong!", serializer.errors)
        else:
            if request.accepted_renderer.format == 'html':
                messages.error(request, "You are not authorized to perform this action")
                return redirect(reverse('todo_list'))
            else:
                return create_api_response(status.HTTP_400_BAD_REQUEST, "You are not authorized to perform this action")
                

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