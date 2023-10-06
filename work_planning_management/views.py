from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics, permissions, filters,status
from requirement_management.models import Requirement
from rest_framework.renderers import TemplateHTMLRenderer, JSONRenderer
from requirement_management.models import Quotation
from .serializers import QuotationSerializer
from django.shortcuts import render
from django.views.generic.base import View
from drf_yasg.utils import swagger_auto_schema

from infinity_fire_solutions.response_schemas import create_api_response, convert_serializer_errors, render_html_response

class ApprovedQuotationListView(generics.ListAPIView):
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    serializer_class = QuotationSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['customer_id__first_name', 'customer_id__last_name']
    template_name = 'approved_quotation_list.html'

    def get_queryset(self):
        customer_id = self.request.query_params.get('customer_id')
        queryset = Quotation.objects.filter(status="approved")
        if customer_id:
            queryset = queryset.filter(customer_id=customer_id)
        return queryset
    
    def get(self, request, *args, **kwargs):
        customer_id = self.request.query_params.get('customer_id')
        queryset = self.get_queryset()
        customer_data = {}
        if request.accepted_renderer.format == 'html':
            context = {
                'approved_quotation': queryset,
                'customer_id': customer_id,
                'customer_data': customer_data
                }
            return render(request, self.template_name, context)
        else:
            messages.error(request, "You are not authorized to perform this action")
            return Response(status=status.HTTP_403_FORBIDDEN)




from django.contrib import messages
from django.urls import reverse
from django.shortcuts import render, redirect
from django.http import Http404, JsonResponse, HttpResponse, HttpResponseRedirect
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from drf_yasg.utils import swagger_auto_schema

from rest_framework import generics, status, filters
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.renderers import TemplateHTMLRenderer, JSONRenderer

from infinity_fire_solutions.aws_helper import *
from infinity_fire_solutions.permission import *
from infinity_fire_solutions.response_schemas import create_api_response, convert_serializer_errors, render_html_response
from infinity_fire_solutions.utils import docs_schema_response_new

from .models import *
from .serializers  import STWAddSerializer

# Create your views here.
# Define a custom API view for STW search
class STWSearchAPIView(CustomAuthenticationMixin, generics.RetrieveAPIView):
   

    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    swagger_schema = None
    template_name = 'stw_form.html'

    def get(self, request, *args, **kwargs):
        # Get the search term from the query parameter
        search_term = request.GET.get('term')
        data = {}

        if search_term:
            # Filter stw based on the search term
            stw_list = STW.objects.filter(
                Q(action__icontains=search_term) |
                Q(description__icontains=search_term) 
            )

            # Get the email from the stw list
            results = [user.email for user in stw_list]

            data = {'results': results}

        # Create an API response
        return create_api_response(
            status_code=status.HTTP_200_OK,
            message="STW data",
            data=data
        )
    
class STWListAPIView(CustomAuthenticationMixin,generics.ListAPIView):
    serializer_class = STWAddSerializer
    renderer_classes = [TemplateHTMLRenderer,JSONRenderer]
    filter_backends = [filters.SearchFilter]
    search_fields = ['action', 'description','RBNO','UPRN']
    template_name = 'stw_list.html'
    ordering_fields = ['created_at'] 

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
        """
        Get the queryset based on filtering parameters from the request.
        """
        # Call the handle_unauthenticated method to handle unauthenticated access
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self, "survey", HasListDataPermission, 'list'
        )
        # Check if authenticated_user is a redirect response
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect

        
        # Define a mapping of data access values to corresponding filters
        filter_mapping = {
            "self": Q(user_id=self.request.user),
            "all": Q(),  # An empty Q() object returns all data
        }
        # Get the appropriate filter from the mapping based on the data access value,
        # or use an empty Q() object if the value is not in the mapping
        base_queryset = STW.objects.filter(filter_mapping.get(data_access_value, Q())).distinct().order_by('-created_at')

        # Order the queryset based on the 'ordering_fields'
        ordering = self.request.GET.get('ordering')
        if ordering in self.ordering_fields:
            base_queryset = base_queryset.order_by(ordering)

        return base_queryset
    

    common_get_response = {
        status.HTTP_200_OK: 
            docs_schema_response_new(
                status_code=status.HTTP_200_OK,
                serializer_class=serializer_class,
                message = "Data retrieved",
                )
    }

    @swagger_auto_schema(operation_id='STW listing', responses={**common_get_response}) 
    def get(self, request, *args, **kwargs):
        """
        Handle both AJAX (JSON) and HTML requests.
        """
        # Get the filtered queryset using get_queryset method
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self, "survey", HasListDataPermission, 'list'
        )
        # Check if authenticated_user is a redirect response
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect

        queryset = self.get_queryset()
        if request.accepted_renderer.format == 'html':
            context = {'stw_data': queryset}
            return render_html_response(context, self.template_name)
        else:
            serializer = self.serializer_class(queryset, many=True)
            return create_api_response(
                status_code=status.HTTP_200_OK,
                message="Data retrieved",
                data=serializer.data
            )
        

class STWAddAPIView(CustomAuthenticationMixin, generics.CreateAPIView):
    """
    View for adding or updating a stw.
    Supports both HTML and JSON response formats.
    """
    serializer_class = STWAddSerializer
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'stw_form.html'


    def get_queryset(self):
        """
        Get the filtered queryset for STWs based on the authenticated user.
        """
        queryset = STW.objects.filter(pk=self.kwargs.get('pk'),user_id=self.request.user.id).order_by('-created_at').first()
        return queryset

    @swagger_auto_schema(auto_schema=None) 
    def get(self, request, *args, **kwargs):
        """
        Handle GET request to display a form for updating a STW.
        If the STW exists, retrieve the serialized data and render the HTML template.
        If the STW does not exist, render the HTML template with an empty serializer.
        """
        # Call the handle_unauthenticated method to handle unauthenticated access
        authenticated_user, data_access_value = check_authentication_and_permissions(
           self,"survey", HasCreateDataPermission, 'add'
        )
        
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect


        if request.accepted_renderer.format == 'html':
            context = {'serializer':self.serializer_class(context={'request': request})}
            return render_html_response(context,self.template_name)
        else:
            return create_api_response(status_code=status.HTTP_201_CREATED,
                                message="GET Method Not Alloweded",)
        
    common_post_response = {
        status.HTTP_200_OK: 
            docs_schema_response_new(
                status_code=status.HTTP_200_OK,
                serializer_class=serializer_class,
                message = "Congratulations! STW has been added successfully.",
                ),
        status.HTTP_400_BAD_REQUEST: 
            docs_schema_response_new(
                status_code=status.HTTP_400_BAD_REQUEST,
                serializer_class=serializer_class,
                message = "We apologize for the inconvenience, but please review the below information.",
                ),

    }  

    @swagger_auto_schema(operation_id='Add STW', responses={**common_post_response})
    def post(self, request, *args, **kwargs):
        """
        Handle POST request to add a stw.
        """
        # Call the handle_unauthenticated method to handle unauthenticated access
        authenticated_user, data_access_value = check_authentication_and_permissions(
           self,"survey", HasCreateDataPermission, 'add'
        )
        message = "Congratulations! STW has been added successfully."
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.validated_data['user_id'] = request.user  # Assign the current user instance.
            user = serializer.save()
            user.save()
            if request.accepted_renderer.format == 'html':
                messages.success(request, message)
                return redirect(reverse('stw_list'))

            else:
                # Return JSON response with success message and serialized data
                return create_api_response(status_code=status.HTTP_201_CREATED,
                                    message=message,
                                    data=serializer.data
                                    )
        else:
            # Invalid serializer data
            if request.accepted_renderer.format == 'html':
                # Render the HTML template with invalid serializer data
                context = {'serializer':serializer}
                return render_html_response(context,self.template_name)
            else:   
                # Return JSON response with error message
                return create_api_response(status_code=status.HTTP_400_BAD_REQUEST,
                                    message="We apologize for the inconvenience, but please review the below information.",
                                    data=convert_serializer_errors(serializer.errors))
            

class STWUpdateView(CustomAuthenticationMixin, generics.UpdateAPIView):
    serializer_class = STWAddSerializer
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'stw_form.html'


    
    def get_queryset(self):
        """
        Get the queryset for listing stw items.

        Returns:
            QuerySet: A queryset of stw items filtered based on the authenticated user's ID.
        """
        
        # Get the model class using the provided module_name string
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self, "survey", HasUpdateDataPermission, 'change'
        )
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect

        # Define a mapping of data access values to corresponding filters
        filter_mapping = {
            "self": Q(user_id=self.request.user ),
            "all": Q(),  # An empty Q() object returns all data
        }

        queryset = STW.objects.filter(filter_mapping.get(data_access_value, Q()))

        # Filter the queryset based on the provided 'stw_id'
        stw_id = self.kwargs.get('stw_id')
        instance = queryset.filter(pk=stw_id).first()
        return instance

    @swagger_auto_schema(auto_schema=None) 
    def get(self, request, *args, **kwargs):
        # This method handles GET requests for updating an existing STW object.
        if request.accepted_renderer.format == 'html':
            instance = self.get_queryset()
            print(instance)
            if instance:
                serializer = self.serializer_class(instance=instance, context={'request': request})
                context = {'serializer': serializer, 'stw_instance': instance,'is_edit': True}
                return render_html_response(context, self.template_name)
            else:
                messages.error(request, "You are not authorized to perform this action")
                return redirect(reverse('stw_list'))
            
    common_put_response = {
        status.HTTP_200_OK: 
            docs_schema_response_new(
                status_code=status.HTTP_200_OK,
                serializer_class=serializer_class,
                message = "STW has been updated successfully!",
                ),
        status.HTTP_400_BAD_REQUEST: 
            docs_schema_response_new(
                status_code=status.HTTP_400_BAD_REQUEST,
                serializer_class=serializer_class,
                message = "You are not authorized to perform this action",
                ),

    }

    @swagger_auto_schema(auto_schema=None) 
    def put(self, request, *args, **kwargs):
        pass

    @swagger_auto_schema(auto_schema=None) 
    def patch(self, request, *args, **kwargs):
        pass

    @swagger_auto_schema(operation_id='Edit STW', responses={**common_put_response})
    def post(self, request, *args, **kwargs):
        """
        Handle POST request to update a  stw instance.

        Args:
            request (rest_framework.request.Request): The HTTP request object.
            *args: Variable-length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            rest_framework.response.Response: HTTP response object.
                If successful, the STW is updated, and the appropriate response is returned.
                If unsuccessful, an error response is returned.
        """
        data = request.data
        instance = self.get_queryset()
        if instance:
            # If the stw instance exists, initialize the serializer with instance and provided data.
            serializer = self.serializer_class(instance=instance, data=data, context={'request': request})

            if serializer.is_valid():
                # If the serializer data is valid, save the updated stw instance.
                serializer.save()
                message = "STW has been updated successfully!"

                if request.accepted_renderer.format == 'html':

                    # For HTML requests, display a success message and redirect to stw.

                    messages.success(request, message)
                    return redirect(reverse('stw_list'))
                else:
                    # For API requests, return a success response with serialized data.
                    return Response({'message': message, 'data': serializer.data}, status=status.HTTP_200_OK)
            else:
                if request.accepted_renderer.format == 'html':
                    # For HTML requests with invalid data, render the template with error messages.
                    context = {'serializer': serializer, 'stw_instance': instance}
                    return render(request, self.template_name, context)
                else:
                    # For API requests with invalid data, return an error response with serializer errors.
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            error_message = "You are not authorized to perform this action"
            if request.accepted_renderer.format == 'html':

                # For HTML requests with no instance, display an error message and redirect to stw.

                messages.error(request, error_message)
                return redirect('stw_list')

            else:
                # For API requests with no instance, return an error response with an error message.
                return Response({'message': error_message}, status=status.HTTP_400_BAD_REQUEST)
            
class STWDeleteView(CustomAuthenticationMixin, generics.DestroyAPIView):
    """
    View for deleteing .
    Supports both HTML and JSON response formats.
    """
    serializer_class = STWAddSerializer
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'stw_form.html'


    common_delete_response = {
        status.HTTP_200_OK: 
            docs_schema_response_new(
                status_code=status.HTTP_200_OK,
                serializer_class=serializer_class,
                message = "STW has been deleted successfully!",
                ),
        status.HTTP_404_NOT_FOUND: 
            docs_schema_response_new(
                status_code=status.HTTP_404_NOT_FOUND,
                serializer_class=serializer_class,
                message = "STW not found OR You are not authorized to perform this action.",
                ),

    }
    @swagger_auto_schema(operation_id='Delete STW', responses={**common_delete_response})
    def delete(self, request, *args, **kwargs):
        """
        Handle DELETE request to delete a STW.
        """

        # Get the STW ID from the URL kwargs
        stw_id = kwargs.get('stw_id')

        # Get the STW instance from the database
        # Call the handle_unauthenticated method to handle unauthenticated access

        authenticated_user, data_access_value = check_authentication_and_permissions(
            self,"survey", HasDeleteDataPermission, 'delete'
        )
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect

        # Define a mapping of data access values to corresponding filters
        filter_mapping = {
            "self": Q(user_id=request.user ),
            "all": Q(),  # An empty Q() object returns all data
        }

        # Get the appropriate filter from the mapping based on the data access value,
        # or use an empty Q() object if the value is not in the mapping

        queryset = STW.objects.filter(filter_mapping.get(data_access_value, Q()))

        stw = queryset.filter(id=stw_id).first()


        
        if stw:
            # Proceed with the deletion
            stw.delete()
            messages.success(request, "STW has been deleted successfully!")
            return create_api_response(status_code=status.HTTP_404_NOT_FOUND,
                                        message="STW has been deleted successfully!", )
        else:
            messages.error(request, "STW not found OR You are not authorized to perform this action.")
            return create_api_response(status_code=status.HTTP_404_NOT_FOUND,
                                        message="STW not found OR You are not authorized to perform this action.", )


class STWDetailView(CustomAuthenticationMixin,generics.RetrieveAPIView):
    """

    View to get the stw.

    Supports both HTML and JSON response formats.
    """
    renderer_classes = [TemplateHTMLRenderer,JSONRenderer]
    template_name = 'stw_view.html'
    serializer_class = STWAddSerializer
    
    def get(self, request, *args, **kwargs):
        # Get the filtered queryset using get_queryset method
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self, "survey", HasViewDataPermission, 'view'
        )
        # Check if authenticated_user is a redirect response
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect

        # Define a mapping of data access values to corresponding filters
        filter_mapping = {
            "self": Q(user_id=self.request.user),
            "all": Q(),  # An empty Q() object returns all data
        }
        # Get the appropriate filter from the mapping based on the data access value,
        # or use an empty Q() object if the value is not in the mapping
        base_queryset = STW.objects.filter(filter_mapping.get(data_access_value, Q())).distinct().order_by('-created_at')
        
        # Get the STW object using the provided 'stw_id'
        stw_id = kwargs.get('stw_id')
        stw = base_queryset.filter(pk=stw_id).first()
        
        
        if stw:
            # Serialize the STW data
            serializer = self.serializer_class(instance=stw, context={'request': request})
            if request.accepted_renderer.format == 'html':
                context = {
                    'serializer': serializer,
                    'stw_instance': stw,
                }
                return render(request, self.template_name, context)
            elif request.accepted_renderer.format == 'json':
                # Return JSON response
                return Response(serializer.data)
        else:
            messages.error(request, "The specified STW does not exist or you are not authorized to view it.")
            return redirect(reverse('stw_list'))
            
