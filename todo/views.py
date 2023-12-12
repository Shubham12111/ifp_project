from django.http import JsonResponse
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.renderers import TemplateHTMLRenderer,JSONRenderer
from infinity_fire_solutions.response_schemas import create_api_response, render_html_response
from .models import *
from datetime import date,timedelta,datetime
from .serializers import *
from django.contrib import messages 
from django.shortcuts import redirect
from django.urls import reverse
from infinity_fire_solutions.permission import *
from rest_framework import filters
from django.apps import apps
from django.db.models import Q
from django.http import  HttpResponse
from authentication.models import *
from datetime import datetime
from drf_yasg.utils import swagger_auto_schema
from infinity_fire_solutions.utils import docs_schema_response_new
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

class ToDoUserSearchAPIView(CustomAuthenticationMixin, generics.RetrieveAPIView):
    """
    API view to search for users by email.

    This view allows searching for users by email and returns a list of matching user emails.
    """
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    swagger_schema = None
    template_name = 'todo_list.html'

    def get(self, request, *args, **kwargs):
        # Get the search term from the request's query parameters
        search_term = request.GET.get('term')
        data = {}
        if search_term:
            # Filter users whose email contains the search term
            user_list = User.objects.filter(Q(first_name__icontains=search_term))

            # Get the usernames from the user_list
            results = [user.first_name for user in user_list]

            data = {'results': results}
            return create_api_response(status_code=status.HTTP_200_OK,
                                       message="User data",
                                       data=data)


class ToDoListAPIView(CustomAuthenticationMixin,generics.ListAPIView):

    """
    API view to list TODO items.
    """
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    ordering_fields = ['created_at']  # Specify fields you want to allow ordering on
    search_fields = ['title']  # Specify fields you want to allow searching on
    template_name = 'todo_list.html'
    serializer_class = TodoListSerializer

    def get_paginated_queryset(self, base_queryset):
        items_per_page = 10 
        paginator = Paginator(base_queryset, items_per_page)
        page_number = self.request.GET.get('page')
        
        try:
            current_page = paginator.page(page_number)
        except PageNotAnInteger:
            # If page is not an integer, deliver the first page.
            current_page = paginator.page(1)
        except EmptyPage:
            # If page is out of range, deliver the last page of results.
            current_page = paginator.page(paginator.num_pages)
        
        return current_page

    def get_queryset(self):
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self, "task", HasListDataPermission, 'list'
        )
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect

        # Define a mapping of data access values to corresponding filters
        filter_mapping = {
            "self": Q(user_id=self.request.user) | Q(assigned_to=self.request.user),
            "all": Q(),  # An empty Q() object returns all data
        }
        # Get the appropriate filter from the mapping based on the data access value,
        # or use an empty Q() object if the value is not in the mapping
        base_queryset = Todo.objects.filter(filter_mapping.get(data_access_value, Q())).distinct().order_by('-created_at')
        
        # Get the filtering parameters from the request's query parameters
        filters = {
            'status': self.request.GET.get('status'),
            'priority': self.request.GET.get('priority'),
            'module': self.request.GET.get('module'),
            'assigned_to': self.request.GET.get('assigned_to'),
            'dateRange': self.request.GET.get('dateRange'),
        }
        date_format = '%d/%m/%Y'

        # Apply additional filters based on the received parameters
        for filter_name, filter_value in filters.items():
            if filter_value:
                if filter_name == 'dateRange':
                    # If 'dateRange' parameter is provided, filter TODO items within the date range
                    start_date_str, end_date_str = filter_value.split('-')
                    start_date = datetime.strptime(start_date_str.strip(), date_format).date()
                    end_date = datetime.strptime(end_date_str.strip(), date_format).date()
                    base_queryset = base_queryset.filter(start_date__gte=start_date, end_date__lte=end_date)
                else:
                    # For other filters, apply the corresponding filters on the queryset
                    filter_mapping = {
                        'status': 'status',
                        'priority': 'priority',
                        'module': 'module__name',
                        'assigned_to': 'assigned_to__first_name',

                    }
                    base_queryset = base_queryset.filter(**{filter_mapping[filter_name]: filter_value})

        # Sort the queryset by 'created_at' in descending order
        base_queryset = self.get_paginated_queryset(base_queryset.order_by('-created_at'))
        return base_queryset
    
    def get_module_list(self):
        """
        Get a list of all unique module names from the Module model.
        """
        return Module.objects.values_list('name', flat=True).distinct()

    def get_assigned_to_users(self):
        """
        Get a list of all unique assigned_to users from the User model.
        """
        return User.objects.values_list('first_name', flat=True).distinct()
    
    common_list_response = {
    status.HTTP_200_OK: 
        docs_schema_response_new(
            status_code=status.HTTP_200_OK,
            serializer_class=serializer_class,
            message = "Task data retrieved successfully.",
            )
    }
    
    @swagger_auto_schema(operation_id='Todo Listing', responses={**common_list_response})
    def get(self, request, *args, **kwargs):
        """
        List view for TODO items.

        Args:
            request (Request): The request object.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Response: The response containing the list of TODO items.
        """
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self, "task", HasListDataPermission, 'list'
        )
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect


        queryset = self.get_queryset()

        queryset = self.filter_queryset(queryset)
        module_list = self.get_module_list()
        assigned_to_users = self.get_assigned_to_users()

        if request.accepted_renderer.format == 'html':
            # If the client accepts HTML, render the template
            context = {'todo_list': queryset,
                    'status_values': STATUS_CHOICES,
                    'module_list': module_list,
                    'assigned_to_users': assigned_to_users,
                    'priority_list': PRIORITY_CHOICES,}
            return render_html_response(context, self.template_name)
        else:
            # If the client accepts other formats, serialize the data and return an API response
            serializer = self.serializer_class(queryset, many=True)
            return create_api_response(
                status_code=status.HTTP_200_OK,
                message="Task data retrieved successfully",
                data=serializer.data
            )
    

class ToDoAddView(CustomAuthenticationMixin, generics.CreateAPIView):

    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'todo_form.html'
    serializer_class = TodoAddSerializer

    @swagger_auto_schema(auto_schema=None) 
    def get(self, request, *args, **kwargs):
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self,"task", HasCreateDataPermission, 'add'
        )
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect

        serializer = self.serializer_class(context={'request': request})

        if request.accepted_renderer.format == 'html':
            # If the client accepts HTML, render the template
            context = {'serializer':serializer}
            return render_html_response(context,self.template_name)
    
    common_post_response = {
        status.HTTP_201_CREATED: 
            docs_schema_response_new(
                status_code=status.HTTP_201_CREATED,
                serializer_class=TodoAddSerializer,
                message = "Your Task has been saved successfully!",
                ),
        status.HTTP_400_BAD_REQUEST: 
            docs_schema_response_new(
                status_code=status.HTTP_400_BAD_REQUEST,
                serializer_class=serializer_class,
                message = "Something went wrong!",
                )
        } 

    @swagger_auto_schema(operation_id='Todo Add', responses={**common_post_response})
    def post(self, request, *args, **kwargs):
        authenticated_user, data_access_value = check_authentication_and_permissions(
           self,"task", HasCreateDataPermission, 'add'
        )
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect

        serializer = self.serializer_class(data=request.data,context={'request': request})

        if serializer.is_valid():
            serializer.validated_data['user_id'] = request.user
            serializer.save()
            message = "Your Task has been saved successfully!"
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
    """
    API view for todo a todo.

    This view handles both HTML and API requests for updating a todo instance.
    If the todo instance exists, it will be updated with the provided data.
    Otherwise, an error message will be returned.

    The following request methods are supported:
    - POST: Updates the todo instance.

    Note: Make sure to replace 'your_template_name.html' with the appropriate HTML template name.
    """
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'todo_form.html'
    serializer_class = TodoAddSerializer

    
    def get_queryset(self):
        """
        Get the queryset for listing TODO items.

        Returns:
            QuerySet: A queryset of TODO items filtered based on the authenticated user's ID.
        """
        # Get the model class using the provided module_name string
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self, "task", HasUpdateDataPermission, 'change'
        )
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect

        # Define a mapping of data access values to corresponding filters
        filter_mapping = {
            "self": Q(user_id=self.request.user ) | Q(assigned_to=self.request.user ),
            "all": Q(),  # An empty Q() object returns all data
        }

        # Get the appropriate filter from the mapping based on the data access value,
        # or use an empty Q() object if the value is not in the mapping
        queryset = Todo.objects.filter(filter_mapping.get(data_access_value, Q())).distinct().order_by('-created_at')
        queryset = queryset.filter(pk=self.kwargs.get('pk')).first()
        
        return queryset

    @swagger_auto_schema(auto_schema=None)     
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
    
    
    @swagger_auto_schema(auto_schema=None) 
    def put(self, request, *args, **kwargs):
        pass

    @swagger_auto_schema(auto_schema=None) 
    def patch(self, request, *args, **kwargs):
        pass
    
    common_post_response = {
        status.HTTP_200_OK: 
            docs_schema_response_new(
                status_code=status.HTTP_200_OK,
                serializer_class=serializer_class,
                message = "Your Task has been updated successfully!",
                ),
        status.HTTP_400_BAD_REQUEST: 
            docs_schema_response_new(
                status_code=status.HTTP_400_BAD_REQUEST,
                serializer_class=serializer_class,
                message = "You are not authorized to perform this action",
                ),

    }
    
    @swagger_auto_schema(operation_id='Todo Edit', responses={**common_post_response})
    def post(self, request, *args, **kwargs):
        """
        Handle POST request to update a todo instance.

        Args:
            request (rest_framework.request.Request): The HTTP request object.
            *args: Variable-length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            rest_framework.response.Response: HTTP response object.
                If successful, the todo is updated, and the appropriate response is returned.
                If unsuccessful, an error response is returned.
        """
        
        data = request.data
        instance = self.get_queryset()
        if instance and instance.status != 'completed':
            # If the todo instance exists, initialize the serializer with instance and provided data.
            serializer = self.serializer_class(instance=instance, data=data, context={'request': request})
            if serializer.is_valid():
                # If the serializer data is valid, save the updated todo instance.
                serializer.save()
                message = "Your TODO has been updated successfully!"
                status_code = status.HTTP_200_OK
                if request.accepted_renderer.format == 'html':
                    # For HTML requests, display a success message and redirect to todo list.
                    messages.success(request,message)
                    return redirect(reverse('todo_list'))
                else:
                    messages.success(request, message)
                    return create_api_response(status_code, f"{message}", serializer.data)
            else:
                if request.accepted_renderer.format == 'html':
                    context = {'serializer': serializer, 'instance': instance}
                    return render_html_response(context, self.template_name)
                else:
                    # For API requests with invalid data, return an error response with serializer errors.
                    return create_api_response(status.HTTP_400_BAD_REQUEST, "Something went wrong!", serializer.errors)
        else:
            if request.accepted_renderer.format == 'html':
                # For HTML requests with no instance, display an error message and redirect to todo_list.
                messages.error(request, "You are not authorized to perform this action")
                return redirect(reverse('todo_list'))
            else:
                # For API requests with no instance, return an error response with an error message.
                return create_api_response(status.HTTP_400_BAD_REQUEST, "You are not authorized to perform this action")
                

class ToDoDeleteView(CustomAuthenticationMixin, generics.DestroyAPIView):

    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    serializer_class = TodoAddSerializer
    
    def get_model_name(self):
        return self.serializer_class.Meta.model.__name__
    
    common_delete_response = {
        status.HTTP_200_OK: 
            docs_schema_response_new(
                status_code=status.HTTP_200_OK,
                serializer_class=serializer_class,
                message = "Your Task has been deleted successfully!",
                ),
        status.HTTP_404_NOT_FOUND: 
            docs_schema_response_new(
                status_code=status.HTTP_404_NOT_FOUND,
                serializer_class=serializer_class,
                message = "Task not found OR You are not authorized to perform this action.",
                ),

    }
    @swagger_auto_schema(operation_id='Todo Delete', responses={**common_delete_response})
    def delete(self, request, *args, **kwargs):
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self,"task", HasDeleteDataPermission, 'delete'
        )
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect

        # Define a mapping of data access values to corresponding filters
        filter_mapping = {
            "self": Q(user_id=request.user ) | Q(assigned_to=request.user ),
            "all": Q(),  # An empty Q() object returns all data
        }

        # Get the appropriate filter from the mapping based on the data access value,
        # or use an empty Q() object if the value is not in the mapping
        queryset = Todo.objects.filter(filter_mapping.get(data_access_value, Q()), pk=self.kwargs.get('pk')).distinct().order_by('-created_at')
        instance = queryset.first()
        
        if instance:
            instance.delete()

            messages.success(request, "Your Task has been deleted successfully!")
            return create_api_response(status_code=status.HTTP_200_OK,
                                        message="Your Task has been deleted successfully!", )

        else:
            messages.error(request, "Todo not found OR You are not authorized to perform this action")
            return create_api_response(status_code=status.HTTP_404_NOT_FOUND)

class ToDoRetrieveAPIView(CustomAuthenticationMixin, generics.RetrieveAPIView):
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    serializer_class = CommentSerializer
    template_name = 'todo_view.html'
    swagger_schema = None

    def get_queryset(self):
        """
        Get the queryset for listing TODO items.

        Returns:
            QuerySet: A queryset of TODO items filtered based on the authenticated user's ID.
        """
        # Get the model class using the provided module_name string
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self,"task", HasViewDataPermission, 'view'
        )
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect

        
        # Define a mapping of data access values to corresponding filters
        filter_mapping = {
            "self": Q(user_id=self.request.user ) | Q(assigned_to=self.request.user ),
            "all": Q(),  # An empty Q() object returns all data
        }

        # Get the appropriate filter from the mapping based on the data access value,
        # or use an empty Q() object if the value is not in the mapping
        queryset = Todo.objects.filter(filter_mapping.get(data_access_value, Q())).distinct().order_by('-created_at')
        queryset = queryset.filter(pk=self.kwargs.get('todo_id')).first()
        
        return queryset

    def get_comment_queryset(self):
        todo_queryset = self.get_queryset()
        queryset = Comment.objects.filter(todo_id=todo_queryset).order_by('-created_at')
        return queryset

    def get(self, request, *args, **kwargs):
        instance = self.get_queryset()
        if request.accepted_renderer.format == 'html':
            # If the client accepts HTML, render the template
            comment_id = self.kwargs.get('comment_id')
            if comment_id:
                comment_instance =  Comment.objects.filter(todo_id=instance,pk=comment_id, user_id=request.user).get()
                serializer = self.serializer_class(instance=comment_instance)
            else:
                serializer =  self.serializer_class()
            
            comment_list = self.get_comment_queryset()
            context = {'todo_data': instance,
                       'serializer':serializer,
                       'comment_list':comment_list}
            return render_html_response(context,self.template_name)
       
    
    def post(self, request, *args, **kwargs):
        todo_data = self.get_queryset()
    

        data = request.data
        if todo_data:
            # If a primary key is provided, it means we are updating an existing todo
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
                if serializer.data.get('status') == 'completed':
                    todo_data.completed_at = datetime.now() 
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
    swagger_schema = None

    def get_app_name(self):
        return apps.get_containing_app_config(self.__module__).name
    
    def get_queryset(self):
        user_id = self.request.user.id
        return Todo.objects.filter(pk=self.kwargs.get('todo_id'))
    
    def destroy(self, request, *args, **kwargs):
        todo = self.get_queryset()
        comment_id = kwargs.get('comment_id')
        if comment_id:
            comment = Comment.objects.filter(todo_id=todo.get(), user_id=request.user , pk=comment_id)
            comment.delete()
            messages.success(request, "Your comment has been deleted successfully!")
            return create_api_response(status_code=status.HTTP_200_OK,
                                        message="Your comment has been deleted successfully!", )
        else:
            messages.error(request, "Comment not found OR You are not authorized to perform this action.")
            return create_api_response(status_code=status.HTTP_404_NOT_FOUND)

