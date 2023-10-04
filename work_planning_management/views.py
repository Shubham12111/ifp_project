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
from .serializers  import STWRequirementSerializer,CustomerSerializer



def get_customer_data(customer_id):

    """
    Get customer data by customer ID.

    Args:
        customer_id (int): The ID of the customer.

    Returns:
        User: The customer data if found, otherwise None.
    """
    customer_data = User.objects.filter(id=customer_id, is_active=True,
                                        roles__name__icontains='customer').first()
    
    return customer_data

def filter_requirements(data_access_value, user, customer=None):
    """
    Filter STW Requirement objects based on data access and user roles.

    This function filters STW Requirement objects based on the data access value and user roles.
    It applies appropriate filters to return a queryset of STW Requirement objects.

    Args:
        data_access_value (str): The data access value.
        user (User): The authenticated user.
        customer (User, optional): The customer for which to filter STW Requirements. Defaults to None.

    Returns:
        QuerySet: A filtered queryset of STW Requirement objects.
    """
    # Define a mapping of data access values to corresponding filters.
    filter_mapping = {
        "self": Q(user_id=user),
        "all": Q(),  # An empty Q() object returns all data.
    }

    if customer:
        queryset = STWRequirements.objects.filter(customer_id=customer)
    else: 
        queryset = queryset.filter(filter_mapping.get(data_access_value, Q()))

    return queryset 


class STWCustomerListView(CustomAuthenticationMixin,generics.ListAPIView):
    """
    View for listing stw Requirement customers.

    This view lists STW Requirement customers, optionally filtered and searchable.
    It provides both HTML and JSON rendering.

    Attributes:
        serializer_class (STWCustomerSerializer): The serializer class.
        renderer_classes (list): The renderer classes for HTML and JSON.
        filter_backends (list): The filter backends, including search filter.
        search_fields (list): The fields for search.
        template_name (str): The template name for HTML rendering.
        ordering_fields (list): The fields for ordering.
    """

    serializer_class = CustomerSerializer
    renderer_classes = [TemplateHTMLRenderer,JSONRenderer]
    filter_backends = [filters.SearchFilter]
    search_fields = ['customer_id__first_name', 'customer_id__last_name']
    template_name = 'stw_customer_list.html'
    ordering_fields = ['created_at'] 

    def get_queryset(self):
            """
        Get the queryset of stw Requirement customers.

        Returns:
            QuerySet: A queryset of stw Requirement customers.
        """
            queryset = User.objects.filter(is_active=True,  roles__name__icontains='customer').exclude(pk=self.request.user.id)
            return queryset
        


    def get(self, request, *args, **kwargs):
        """
        Handle GET requests for listing STW Requirement customers.

        Args:
            request (HttpRequest): The HTTP request object.

        Returns:
            HttpResponse: The response, either HTML or JSON.
        """
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self, "survey", HasListDataPermission, 'list'
        )
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect

        queryset = self.get_queryset()
        all_stw = STWRequirements.objects.filter()
        
        customers_with_counts = []  # Create a list to store customer objects with counts

        for customer in queryset:
            stw_counts = all_stw.filter(customer_id=customer).count()
            customers_with_counts.append({'customer': customer, 'stw_counts': stw_counts})

        if request.accepted_renderer.format == 'html':
            context = {'customers_with_counts': customers_with_counts}  # Pass the list of customers with counts to the template
            return render_html_response(context, self.template_name)
        else:
            serializer = self.serializer_class(queryset, many=True)
            return create_api_response(status_code=status.HTTP_200_OK,
                                    message="Data retrieved",
                                    data=serializer.data)
        
class STWRequirementListView(CustomAuthenticationMixin,generics.ListAPIView):
    """
    View to get the listing of all stw requirements.
    Supports both HTML and JSON response formats.
    """
    serializer_class = STWRequirementSerializer
    renderer_classes = [TemplateHTMLRenderer,JSONRenderer]
    filter_backends = [filters.SearchFilter]
    search_fields = ['action', 'description','RBNO','UPRN']
    template_name = 'stw_list.html'
    ordering_fields = ['created_at'] 

    common_get_response = {
    status.HTTP_200_OK: 
        docs_schema_response_new(
            status_code=status.HTTP_200_OK,
            serializer_class=serializer_class,
            message = "Data retrieved",
            )
    }
    
    @swagger_auto_schema(operation_id='STW Requirement Listing', responses={**common_get_response})
    def get(self, request, *args, **kwargs):

        """
        Handle both AJAX (JSON) and HTML requests.
        """
        customer_id = kwargs.get('customer_id', None)
        
        customer_data = User.objects.filter(id=customer_id).first()
        
        if customer_data:
            # Call the handle_unauthenticated method to handle unauthenticated access.
            authenticated_user, data_access_value = check_authentication_and_permissions(
                self,"survey", HasListDataPermission, 'list'
            )
            if isinstance(authenticated_user, HttpResponseRedirect):
                return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect

            queryset = filter_requirements(data_access_value, self.request.user, customer_data)


            if request.accepted_renderer.format == 'html':
                context = {'stw_requirements':queryset, 'customer_id':customer_id,
                        'customer_data':customer_data,
                     }
                return render_html_response(context,self.template_name)
            else:
                serializer = self.serializer_class(queryset, many=True)
                return create_api_response(status_code=status.HTTP_200_OK,
                                                message="Data retrieved",
                                                data=serializer.data)
        else:
            messages.error(request, "You are not authorized to perform this action")
            return redirect(reverse('customer_stw_list', kwargs={'customer_id': customer_id}))  
        
        
        
class STWRequirementAddView(CustomAuthenticationMixin, generics.CreateAPIView):
    """
    View for adding  a STW requirement.
    Supports both HTML and JSON response formats.
    """
    serializer_class = STWRequirementSerializer
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'stw_form.html'
    
    @swagger_auto_schema(auto_schema=None) 
    def get(self, request, *args, **kwargs):
        """
        Handle GET request to display a form for adding a STW requirement.
        If the STW requirement exists, retrieve the serialized data and render the HTML template.
        If the STW requirement does not exist, render the HTML template with an empty serializer.
        """
        customer_id = kwargs.get('customer_id', None)
        
        customer_data = User.objects.filter(id=customer_id).first()
        
        if customer_data:
            # Call the handle_unauthenticated method to handle unauthenticated access
            authenticated_user, data_access_value = check_authentication_and_permissions(
            self,"survey", HasCreateDataPermission, 'add'
            )

            if isinstance(authenticated_user, HttpResponseRedirect):
                return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect

            # Filter the queryset based on the user ID
            serializer = self.serializer_class(context={'request': request})
            
            if request.accepted_renderer.format == 'html':
                context = {'serializer':serializer, 
                           'customer_id': kwargs.get('customer_id'),
                           'customer_data':customer_data}
                
                return render_html_response(context,self.template_name)
            else:
                return create_api_response(status_code=status.HTTP_201_CREATED,
                                    message="GET Method Not Alloweded",)
        else:
            messages.error(request, "You are not authorized to perform this action")
            return redirect(reverse('customer_stw_list', kwargs={'customer_id': customer_id}))

  
    def post(self, request, *args, **kwargs):
        """
        Handle POST request to add a STW requirement.
        """
        customer_id = kwargs.get('customer_id', None)
        
        customer_data = User.objects.filter(id=customer_id).first()
        
        if customer_data:
            data = request.data

            file_list = data.getlist('file_list', [])
            
            if not any(file_list):
                data = data.copy()      # make a mutable copy of data before performing delete.
                del data['file_list']
            
            serializer_data = request.data if any(file_list) else data
            
            serializer = self.serializer_class(data=serializer_data, context={'request': request})
            
            message = "Congratulations! your STW Requirement has been added successfully."
            if serializer.is_valid():
                serializer.validated_data['user_id'] = request.user  # Assign the current user instance.
                serializer.validated_data['customer_id'] = customer_data
                serializer.save()

                if request.accepted_renderer.format == 'html':
                    messages.success(request, message)
                    return redirect(reverse('customer_stw_list', kwargs={'customer_id': customer_id}))

                else:
                    # Return JSON response with success message and serialized data.
                    return create_api_response(status_code=status.HTTP_201_CREATED,
                                        message=message,
                                        data=serializer.data
                                        )
            else:
                # Invalid serializer data.
                if request.accepted_renderer.format == 'html':
                    # Render the HTML template with invalid serializer data.
                    context = {'serializer':serializer, 
                           'customer_id': kwargs.get('customer_id'),
                           'customer_data':customer_data}
                    return render_html_response(context,self.template_name)
                else:   
                    # Return JSON response with error message.
                    return create_api_response(status_code=status.HTTP_400_BAD_REQUEST,
                                        message="We apologize for the inconvenience, but please review the below information.",
                                        data=convert_serializer_errors(serializer.errors))
        else:
            messages.error(request, "You are not authorized to perform this action")
            return redirect(reverse('customer_stw_list', kwargs={'customer_id': customer_id}))  
        

class STWRequirementUpdateView(CustomAuthenticationMixin, generics.UpdateAPIView):
    """
    API view for updating a STW requirement.

    This view handles both HTML and API requests for updating a requirement instance.
    If the STW requirement instance exists, it will be updated with the provided data.
    Otherwise, an error message will be returned.

    The following request methods are supported:
    - POST: Updates the STW requirement instance.

    Note: Make sure to replace 'your_template_name.html' with the appropriate HTML template name.
    """
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'stw_form.html'
    serializer_class = STWRequirementSerializer
    
    def get_queryset(self):
        """
        Get the queryset for listing STW Requirement items.

        Returns:
            QuerySet: A queryset of STW Requirements items filtered based on the authenticated user's ID.
        """
        # Get the model class using the provided module_name string
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self, "survey", HasUpdateDataPermission, 'change'
        )
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect

        queryset = filter_requirements(data_access_value, self.request.user, customer=self.kwargs.get('customer_id'))
        queryset = queryset.filter(pk=self.kwargs.get('pk')).first()
        return queryset

    @swagger_auto_schema(auto_schema=None)
    def get(self, request, *args, **kwargs):
        customer_id = self.kwargs.get('customer_id')
        customer_data = User.objects.filter(id=customer_id).first()
        # This method handles GET requests for updating an existing STW Requirement object.
        if request.accepted_renderer.format == 'html':
            instance = self.get_queryset()
            if instance:
                serializer = self.serializer_class(instance=instance, context={'request': request})
                context = {'serializer': serializer, 'stw_instance': instance, 
                           'customer_id': self.kwargs.get('customer_id'),
                           'customer_data':customer_data}
                return render_html_response(context, self.template_name)
            else:
                messages.error(request, "You are not authorized to perform this action")
                return redirect(reverse('customer_stw_list', kwargs={'customer_id': kwargs.get('customer_id')}))
    
    common_post_response = {
        status.HTTP_200_OK: 
            docs_schema_response_new(
                status_code=status.HTTP_200_OK,
                serializer_class=serializer_class,
                message = "Your STW Requirement has been updated successfully!",
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

    @swagger_auto_schema(operation_id=' STW Requirement Edit', responses={**common_post_response})
    def post(self, request, *args, **kwargs):
        """
        Handle POST request to update a STW requirement instance.

        Args:
            request (rest_framework.request.Request): The HTTP request object.
            *args: Variable-length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            rest_framework.response.Response: HTTP response object.
                If successful, the STW requirement is updated, and the appropriate response is returned.
                If unsuccessful, an error response is returned.
        """
        instance = self.get_queryset()
        if instance:
            data = request.data
    
            file_list = data.getlist('file_list', [])
            
            if not any(file_list):
                data = data.copy()      # make a mutable copy of data before performing delete.
                del data['file_list']
            
            serializer_data = request.data if any(file_list) else data
            serializer_data['RBNO'] = instance.RBNO
            serializer_data['UPRN'] = instance.UPRN
            serializer = self.serializer_class(instance=instance, data=serializer_data, context={'request': request})

            if serializer.is_valid():
                # If the serializer data is valid, save the updated STW requirement instance.
                serializer.update(instance, validated_data=serializer.validated_data)
                message = "Your STW requirement has been updated successfully!"

                if request.accepted_renderer.format == 'html':
                    # For HTML requests, display a success message and redirect to customer_stw_list.
                    messages.success(request, message)
                    return redirect(reverse('customer_stw_list', kwargs={'customer_id': kwargs.get('customer_id')}))
                else:
                    # For API requests, return a success response with serialized data.
                    return Response({'message': message, 'data': serializer.data}, status=status.HTTP_200_OK)
            else:
                if request.accepted_renderer.format == 'html':
                    # For HTML requests with invalid data, render the template with error messages.
                    context = {'serializer': serializer,
                     'stw_instance': instance,'customer_id':kwargs.get('customer_id')}
                    return render(request, self.template_name, context)
                else:
                    # For API requests with invalid data, return an error response with serializer errors.
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            error_message = "You are not authorized to perform this action"
            if request.accepted_renderer.format == 'html':
                # For HTML requests with no instance, display an error message and redirect to customer_stw_list.
                messages.error(request, error_message)
                return redirect(reverse('customer_stw_list', kwargs={'customer_id': kwargs.get('customer_id')}))
            else:
                # For API requests with no instance, return an error response with an error message.
                return Response({'message': error_message}, status=status.HTTP_400_BAD_REQUEST)
            
class STWRequirementDeleteView(CustomAuthenticationMixin, generics.DestroyAPIView):
    """
    View for deleting a STW requirement.
    Supports both HTML and JSON response formats.
    """
    serializer_class = STWRequirementSerializer
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    
    common_delete_response = {
        status.HTTP_200_OK: 
            docs_schema_response_new(
                status_code=status.HTTP_200_OK,
                serializer_class=serializer_class,
                message = "STW Requirement has been deleted successfully!",
                ),
        status.HTTP_404_NOT_FOUND: 
            docs_schema_response_new(
                status_code=status.HTTP_404_NOT_FOUND,
                serializer_class=serializer_class,
                message = "STW Requirement not found OR You are not authorized to perform this action.",
                ),

    }
    @swagger_auto_schema(operation_id='STW Requirement Delete', responses={**common_delete_response})
    
    def delete(self, request, *args, **kwargs):
        """
        Handle DELETE request to delete a STW requirement.
        """
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self, "survey", HasUpdateDataPermission, 'delete'
        )

        # Get the stw requirement instance from the database.
        # Define a mapping of data access values to corresponding filters
        filter_mapping = {
            "self": Q(user_id=request.user ),
            "all": Q(),  # An empty Q() object returns all data
        }

        # Get the appropriate filter from the mapping based on the data access value,
        # or use an empty Q() object if the value is not in the mapping
        queryset = filter_requirements(data_access_value, self.request.user)
        instance = queryset.filter(pk=self.kwargs.get('pk')).first()
        print(instance)

        if instance:
            # Proceed with the deletion
            instance.delete()
            messages.success(request, "Your STW requirement has been deleted successfully!")
            return create_api_response(status_code=status.HTTP_404_NOT_FOUND,
                                        message="Your STW requirement has been deleted successfully!", )
        else:
            messages.error(request, "STW Requirement not found OR You are not authorized to perform this action.")
            return create_api_response(status_code=status.HTTP_404_NOT_FOUND,
                                        message="STW Requirement not found OR You are not authorized to perform this action.", )
    

class STWRemoveDocumentView(generics.DestroyAPIView):
    """
    View to remove a document associated with a STW requirement.
    """
    swagger_schema = None
    
    def destroy(self, request, *args, **kwargs):
        """
        Handles DELETE request to remove the document associated with a STW requirement.
        """
        stw_id = kwargs.get('stw_id')
        if stw_id:
            stw_instance = STWAsset.objects.filter(stw_id=stw_id, pk=  kwargs.get('document_id')).get()
            if stw_instance and stw_instance.document_path: 
                
                s3_client.delete_object(Bucket=settings.AWS_BUCKET_NAME, Key = stw_instance.document_path)
                stw_instance.delete()
            return Response(
                {"message": "Your STW Requirement has been deleted successfully."},
                status=status.HTTP_204_NO_CONTENT
            )
        else:
            return Response(
                {"message": "Requirement not found OR you don't have permission to delete."},
                status=status.HTTP_404_NOT_FOUND
            )
    

class STWDetailView(CustomAuthenticationMixin,generics.RetrieveAPIView):
    """

    View to get the stw.

    Supports both HTML and JSON response formats.
    """
    renderer_classes = [TemplateHTMLRenderer,JSONRenderer]
    template_name = 'stw_view.html'
    serializer_class = STWRequirementSerializer

    def get_queryset(self):
        """
        Get the queryset for listing STW Requirement items.

        Returns:
            QuerySet: A queryset of STW Requirements items filtered based on the authenticated user's ID.
        """
        # Get the model class using the provided module_name string
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self, "survey", HasViewDataPermission, 'view'
        )
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect

        queryset = filter_requirements(data_access_value, self.request.user, customer=self.kwargs.get('customer_id'))
        queryset =  queryset.filter(pk=self.kwargs.get('pk')).first()
        

        return queryset
    

    @swagger_auto_schema(auto_schema=None)
    def get(self, request, *args, **kwargs):
        """
        Handle GET requests for displaying STW Requirement details.

        Args:
            request (HttpRequest): The HTTP request object.

        Returns:
            HttpResponse: The response, either HTML or JSON.
        """
        customer_id = kwargs.get('customer_id')
        customer_data = User.objects.filter(id=customer_id).first()
        
        if customer_data:
            # This method handles GET requests for updating an existing Requirement object.
            if request.accepted_renderer.format == 'html':
                instance = self.get_queryset()
                if instance:
                    serializer = self.serializer_class(instance=instance, context={'request': request})
                    
                    context = {
                        'serializer': serializer, 
                        'stw_instance': instance, 
                        'customer_id': kwargs.get('customer_id'),
                        'customer_data':customer_data
                        }
               

                    return render_html_response(context, self.template_name)
            else:
                messages.error(request, "You are not authorized to perform this action")
                return redirect(reverse('customer_stw_list', kwargs={'customer_id': kwargs.get('customer_id')}))
    