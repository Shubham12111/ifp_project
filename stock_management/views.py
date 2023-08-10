from django.contrib import messages
from django.urls import reverse
from django.shortcuts import render, redirect
from django.http import Http404, JsonResponse, HttpResponse,HttpResponseRedirect
from django.conf import settings
from drf_yasg.utils import swagger_auto_schema
from django.shortcuts import get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from rest_framework import generics, status, filters
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.renderers import TemplateHTMLRenderer, JSONRenderer

from infinity_fire_solutions.aws_helper import *
from infinity_fire_solutions.permission import *
from infinity_fire_solutions.response_schemas import create_api_response, convert_serializer_errors, render_html_response
from infinity_fire_solutions.utils import docs_schema_response_new

from .models import *

from .serializers import *

from .serializers import VendorSerializer,BillingDetailSerializer





# Create your views here.

class VendorListView(CustomAuthenticationMixin,generics.ListAPIView):
    """

    View to get the listing of all vendors.

    Supports both HTML and JSON response formats.
    """
    serializer_class = VendorSerializer
    renderer_classes = [TemplateHTMLRenderer,JSONRenderer]
    filter_backends = [filters.SearchFilter]
    search_fields = ['first_name', 'last_name','email']
    template_name = 'vendor_list.html'
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
            self, "stock_management", HasListDataPermission, 'list'
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
        base_queryset = Vendor.objects.filter(filter_mapping.get(data_access_value, Q())).distinct().order_by('-created_at')

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

    common_get_response = {
        status.HTTP_200_OK: 
            docs_schema_response_new(
                status_code=status.HTTP_200_OK,
                serializer_class=serializer_class,
                message = "Data retrieved",
                )
    }
    @swagger_auto_schema(operation_id='Vendor listing', responses={**common_get_response}) 
    def get(self, request, *args, **kwargs):
        """
        Handle both AJAX (JSON) and HTML requests.
        """
        # Get the filtered queryset using get_queryset method
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self, "stock_management", HasListDataPermission, 'list'
        )
        # Check if authenticated_user is a redirect response
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect

        queryset = self.get_queryset()
        if request.accepted_renderer.format == 'html':
            context = {'vendors': queryset}
            return render_html_response(context, self.template_name)
        else:
            serializer = self.serializer_class(queryset, many=True)
            return create_api_response(
                status_code=status.HTTP_200_OK,
                message="Data retrieved",
                data=serializer.data
            )
        

class VendorAddView(CustomAuthenticationMixin, generics.CreateAPIView):
    """
    View for adding or updating a vendor.
    Supports both HTML and JSON response formats.
    """
    serializer_class = VendorSerializer
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'vendor.html'


    def get_queryset(self):
        """
        Get the filtered queryset for vendors based on the authenticated user.
        """
        queryset = Vendor.objects.filter(pk=self.kwargs.get('pk'),user_id=self.request.user.id).order_by('-created_at').first()
        return queryset

    @swagger_auto_schema(auto_schema=None) 
    def get(self, request, *args, **kwargs):
        """
        Handle GET request to display a form for updating a vendor.
        If the vendor exists, retrieve the serialized data and render the HTML template.
        If the vendor does not exist, render the HTML template with an empty serializer.
        """
        # Call the handle_unauthenticated method to handle unauthenticated access
        authenticated_user, data_access_value = check_authentication_and_permissions(
           self,"stock_management", HasCreateDataPermission, 'add'
        )
        
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect


        if request.accepted_renderer.format == 'html':
            context = {'serializer':self.serializer_class()}
            return render_html_response(context,self.template_name)
        else:
            return create_api_response(status_code=status.HTTP_201_CREATED,
                                message="GET Method Not Alloweded",)
        
    common_post_response = {
        status.HTTP_200_OK: 
            docs_schema_response_new(
                status_code=status.HTTP_200_OK,
                serializer_class=serializer_class,
                message = "Congratulations! vendor has been added successfully.",
                ),
        status.HTTP_400_BAD_REQUEST: 
            docs_schema_response_new(
                status_code=status.HTTP_400_BAD_REQUEST,
                serializer_class=serializer_class,
                message = "We apologize for the inconvenience, but please review the below information.",
                ),

    }  

    @swagger_auto_schema(operation_id='Add Vendor', responses={**common_post_response})
    def post(self, request, *args, **kwargs):
        """
        Handle POST request to add a vendor.
        """
        # Call the handle_unauthenticated method to handle unauthenticated access
        authenticated_user, data_access_value = check_authentication_and_permissions(
           self,"stock_management", HasCreateDataPermission, 'add'
        )
        message = "Congratulations! vendor has been added successfully."
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.validated_data['user_id'] = request.user  # Assign the current user instance.
            user = serializer.save()
            user.save()
            if request.accepted_renderer.format == 'html':
                messages.success(request, message)
                return redirect(reverse('vendor_list'))

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
            

class VendorUpdateView(CustomAuthenticationMixin, generics.UpdateAPIView):
    """
    API view for updating a vendor.

    This view handles both HTML and API requests for updating a vendor instance.
    If the vendor instance exists, it will be updated with the provided data.
    Otherwise, an error message will be returned.

    The following request methods are supported:
    - POST: Updates the vendor instance.

    Note: Make sure to replace 'your_template_name.html' with the appropriate HTML template name.
    """
    
    serializer_class = VendorSerializer
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'vendor.html'


    
    def get_queryset(self):
        """
        Get the queryset for listing Conatct items.

        Returns:
            QuerySet: A queryset of Conatct items filtered based on the authenticated user's ID.
        """
        
        # Get the model class using the provided module_name string
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self, "stock_management", HasUpdateDataPermission, 'change'
        )
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect

        # Define a mapping of data access values to corresponding filters
        filter_mapping = {
            "self": Q(user_id=self.request.user ),
            "all": Q(),  # An empty Q() object returns all data
        }

        queryset = Vendor.objects.filter(filter_mapping.get(data_access_value, Q()))

        # Filter the queryset based on the provided 'vendor_id'
        vendor_id = self.kwargs.get('vendor_id')
        instance = queryset.filter(pk=vendor_id).first()
        return instance

    @swagger_auto_schema(auto_schema=None) 
    def get(self, request, *args, **kwargs):
        # This method handles GET requests for updating an existing vendor object.
        if request.accepted_renderer.format == 'html':
            instance = self.get_queryset()
            print(instance)
            if instance:
                serializer = self.serializer_class(instance=instance, context={'request': request})
                context = {'serializer': serializer, 'vendor_instance': instance}
                return render_html_response(context, self.template_name)
            else:
                messages.error(request, "You are not authorized to perform this action")
                return redirect(reverse('vendor_list'))
            
    common_put_response = {
        status.HTTP_200_OK: 
            docs_schema_response_new(
                status_code=status.HTTP_200_OK,
                serializer_class=serializer_class,
                message = "Vendor has been updated successfully!",
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

    @swagger_auto_schema(operation_id='Edit Vendor', responses={**common_put_response})
    def post(self, request, *args, **kwargs):
        """
        Handle POST request to update a vendor instance.

        Args:
            request (rest_framework.request.Request): The HTTP request object.
            *args: Variable-length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            rest_framework.response.Response: HTTP response object.
                If successful, the vendor is updated, and the appropriate response is returned.
                If unsuccessful, an error response is returned.
        """
        data = request.data
        instance = self.get_queryset()
        if instance:
            # If the vendor instance exists, initialize the serializer with instance and provided data.
            serializer = self.serializer_class(instance=instance, data=data, context={'request': request})

            if serializer.is_valid():
                # If the serializer data is valid, save the updated vendor instance.
                serializer.save()
                message = "Vendor has been updated successfully!"

                if request.accepted_renderer.format == 'html':

                    # For HTML requests, display a success message and redirect to vendor.

                    messages.success(request, message)
                    return redirect(reverse('vendor_billing_detail', kwargs={'vendor_id': kwargs['vendor_id']}))
                else:
                    # For API requests, return a success response with serialized data.
                    return Response({'message': message, 'data': serializer.data}, status=status.HTTP_200_OK)
            else:
                if request.accepted_renderer.format == 'html':
                    # For HTML requests with invalid data, render the template with error messages.
                    context = {'serializer': serializer, 'instance': instance}
                    return render(request, self.template_name, context)
                else:
                    # For API requests with invalid data, return an error response with serializer errors.
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            error_message = "You are not authorized to perform this action"
            if request.accepted_renderer.format == 'html':

                # For HTML requests with no instance, display an error message and redirect to vendor.

                messages.error(request, error_message)
                return redirect('vendor/vendor_list')

            else:
                # For API requests with no instance, return an error response with an error message.
                return Response({'message': error_message}, status=status.HTTP_400_BAD_REQUEST)
            
class VendorDeleteView(CustomAuthenticationMixin, generics.DestroyAPIView):
    """
    View for deleteing .
    Supports both HTML and JSON response formats.
    """
    serializer_class = VendorSerializer
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'vendor.html'


    common_delete_response = {
        status.HTTP_200_OK: 
            docs_schema_response_new(
                status_code=status.HTTP_200_OK,
                serializer_class=serializer_class,
                message = "Vendor has been deleted successfully!",
                ),
        status.HTTP_404_NOT_FOUND: 
            docs_schema_response_new(
                status_code=status.HTTP_404_NOT_FOUND,
                serializer_class=serializer_class,
                message = "Vendor not found",
                ),

    }
    @swagger_auto_schema(operation_id='Delete Vendor', responses={**common_delete_response})
    def delete(self, request, *args, **kwargs):
        """
        Handle DELETE request to delete a vendor.
        """

        # Get the vendor ID from the URL kwargs
        vendor_id = kwargs.get('pk')

        # Get the vendor instance from the database
        # Call the handle_unauthenticated method to handle unauthenticated access

        authenticated_user, data_access_value = check_authentication_and_permissions(
            self,"stock_management", HasDeleteDataPermission, 'delete'
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

        queryset = Vendor.objects.filter(filter_mapping.get(data_access_value, Q()))

        vendor = queryset.filter(id=vendor_id).first()


        
        if vendor:
            # Proceed with the deletion
            vendor.delete()
            messages.success(request, "Vendor has been deleted successfully!")
            return create_api_response(status_code=status.HTTP_404_NOT_FOUND,
                                        message="Vendor has been deleted successfully!", )
        else:
            messages.error(request, "Vendor not found")
            return create_api_response(status_code=status.HTTP_404_NOT_FOUND,
                                        message="Vendor not found", )
       
class VendorBillingDetailView(CustomAuthenticationMixin, generics.CreateAPIView):
    """
    View for adding or updating a vendor.
    Supports both HTML and JSON response formats.
    """
    serializer_class = BillingDetailSerializer
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'vendor_billing_detail.html'

    def get_billing_detail(self):
        vendor_id = self.kwargs.get('vendor_id')
        billing_address_list = Vendor.objects.filter(id=vendor_id)
        return billing_address_list

   
    def get_queryset(self):
        """
        Get the queryset for listing vendor items.

        Returns:
            QuerySet: A queryset of vendor items filtered based on the authenticated user's ID.
        """
        # Get the model class using the provided module_name string
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self, "stock_management", HasUpdateDataPermission, 'change'
        )
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect

        # Define a mapping of data access values to corresponding filters
        filter_mapping = {
            "self": Q(user_id=self.request.user ),
            "all": Q(),  # An empty Q() object returns all data
        }

        # Get the appropriate filter from the mapping based on the data access value,
        # or use an empty Q() object if the value is not in the mapping
        queryset = Vendor.objects.filter(filter_mapping.get(data_access_value, Q()))
        queryset = queryset.filter(pk=self.kwargs.get('vendor_id')).first()
        return queryset

   
    @swagger_auto_schema(auto_schema=None)    
    def get(self, request, *args, **kwargs):
        """
        Handle GET request to display a form for updating a Vendor.
        If the Vendor exists, retrieve the serialized data and render the HTML template.
        If the Vendor does not exist, render the HTML template with an empty serializer.
        """
        # Call the handle_unauthenticated method to handle unauthenticated access
        authenticated_user, data_access_value = check_authentication_and_permissions(
           self,"stock_management", HasCreateDataPermission, 'change'
        )
        if request.accepted_renderer.format == 'html':
            vendor_instance = self.get_queryset()  # Corrected to retrieve the vendor_instance
            if vendor_instance:
                serializer = self.serializer_class(instance=vendor_instance)  # Prefill the form
        
            billing_detail_list = self.get_billing_detail()  # Retrieve billing details
        
            context = {
                'serializer': serializer,
                'vendor_instance': vendor_instance,
                'billing_detail_list': billing_detail_list,
            }
        
            if vendor_instance:
                return render_html_response(context, self.template_name)
            else:
                messages.error(request, "Vendor not found.")
                return redirect(reverse('vendor_list'))
        else:
            return create_api_response(status_code=status.HTTP_201_CREATED, message="GET Method Not Alloweded")


    common_post_response = {
        status.HTTP_200_OK: 
            docs_schema_response_new(
                status_code=status.HTTP_200_OK,
                serializer_class=serializer_class,
                message = "Vendor billing details have been updated successfully!",
                ),
        status.HTTP_400_BAD_REQUEST: 
            docs_schema_response_new(
                status_code=status.HTTP_400_BAD_REQUEST,
                serializer_class=serializer_class,
                message = "We apologize for the inconvenience, but please review the below information.",
                ),

    }  

    @swagger_auto_schema(operation_id='Add Billing Details', responses={**common_post_response})        
    def post(self, request, *args, **kwargs):
        data = request.data
        vendor_instance = self.get_queryset()
        serializer = self.serializer_class(data=data, context={'request': request})
    
        if vendor_instance:
            # Update existing vendor's billing details
            message = "Vendor billing details have been updated successfully!"
            serializer = self.serializer_class(instance=vendor_instance, data=data, context={'request': request})

        else:
            # Add a new vendor's billing details
            message = "Vendor has been added successfully!"
            serializer = self.serializer_class(data=data, context={'request': request})
    
        if serializer.is_valid():
            # If the serializer data is valid, save the billing address instance.
            serializer.save(vendor=vendor_instance)

            if request.accepted_renderer.format == 'html':
                # For HTML requests, display a success message and redirect to the Vendor's billing address list.
                messages.success(request, message)
                return redirect(reverse('vendor_contact_person', kwargs={'vendor_id': kwargs['vendor_id']}))
            else:
                # For API requests, return a success response with serialized data.
                return Response({'message': message, 'data': serializer.data}, status=status.HTTP_200_OK)
        else:
            if request.accepted_renderer.format == 'html':
                # For HTML requests with invalid data, render the template with error messages.
                context = {'serializer': serializer,
                       'vendor_instance': vendor_instance,
                       'billing_detail_list': self.get_billing_detail()}
                return render(request, self.template_name, context)
            else:
                    # For API requests with invalid data, return an error response with serializer errors.
                return create_api_response(status_code=status.HTTP_400_BAD_REQUEST,
                                    message="We apologize for the inconvenience, but please review the below information.",
                                    data=convert_serializer_errors(serializer.errors))


class VendorRemarkView(CustomAuthenticationMixin, generics.CreateAPIView):
    """
    View for adding or updating a vendor remarks.
    Supports both HTML and JSON response formats.
    """
    serializer_class = VendorRemarkSerializer
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'vendor_remarks.html'

    def get_remarks(self):
        vendor_id = self.kwargs.get('vendor_id')
        remarks_list = Vendor.objects.filter(id=vendor_id)
        return remarks_list

   
    def get_queryset(self):
        """
        Get the queryset for listing vendor remarks items.

        Returns:
            QuerySet: A queryset of vendor remarks items filtered based on the authenticated user's ID.
        """
        # Get the model class using the provided module_name string
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self, "stock_management", HasUpdateDataPermission, 'change'
        )
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect

        # Define a mapping of data access values to corresponding filters
        filter_mapping = {
            "self": Q(user_id=self.request.user ),
            "all": Q(),  # An empty Q() object returns all data
        }

        # Get the appropriate filter from the mapping based on the data access value,
        # or use an empty Q() object if the value is not in the mapping
        queryset = Vendor.objects.filter(filter_mapping.get(data_access_value, Q()))
        queryset = queryset.filter(pk=self.kwargs.get('vendor_id')).first()
        return queryset

   
    @swagger_auto_schema(auto_schema=None)    
    def get(self, request, *args, **kwargs):
        """
        Handle GET request to display a form for updating a Vendor.
        If the Vendor exists, retrieve the serialized data and render the HTML template.
        If the Vendor does not exist, render the HTML template with an empty serializer.
        """
        # Call the handle_unauthenticated method to handle unauthenticated access
        authenticated_user, data_access_value = check_authentication_and_permissions(
           self,"stock_management", HasCreateDataPermission, 'change'
        )
        if request.accepted_renderer.format == 'html':
            vendor_instance = self.get_queryset()  # Corrected to retrieve the vendor_instance
            if vendor_instance:
                serializer = self.serializer_class(instance=vendor_instance)  # Prefill the form
        
            remarks_list = self.get_remarks()  # Retrieve billing details
        
            context = {
                'serializer': serializer,
                'vendor_instance': vendor_instance,
                'remarks_list': remarks_list,
            }
        
            if vendor_instance:
                return render_html_response(context, self.template_name)
            else:
                messages.error(request, "Vendor not found.")
                return redirect(reverse('vendor_list'))
        else:
            return create_api_response(status_code=status.HTTP_201_CREATED, message="GET Method Not Alloweded")


    common_post_response = {
        status.HTTP_200_OK: 
            docs_schema_response_new(
                status_code=status.HTTP_200_OK,
                serializer_class=serializer_class,
                message = "Vendor Remarks have been updated successfully!",
                ),
        status.HTTP_400_BAD_REQUEST: 
            docs_schema_response_new(
                status_code=status.HTTP_400_BAD_REQUEST,
                serializer_class=serializer_class,
                message = "We apologize for the inconvenience, but please review the below information.",
                ),

    }  

    @swagger_auto_schema(operation_id='Add Remarks', responses={**common_post_response})        
    def post(self, request, *args, **kwargs):
        data = request.data
        vendor_instance = self.get_queryset()
        serializer = self.serializer_class(data=data, context={'request': request})
    
        if vendor_instance:
            # Update existing vendor's remarks
            message = "Vendor Remarks have been updated successfully!"
            serializer = self.serializer_class(instance=vendor_instance, data=data, context={'request': request})
        else:
            message = "Vendor Remarks have been added successfully!"
            serializer = self.serializer_class(data=data, context={'request': request})

        if serializer.is_valid():
            # If the serializer data is valid, save the remarks instance.
            serializer.save(vendor=vendor_instance)

            if request.accepted_renderer.format == 'html':
                # For HTML requests, display a success message and redirect to the Vendor's remarks.
                messages.success(request, message)  # Add this line to display the success message
                return redirect(reverse('vendor_list'))
            else:
                # For API requests, return a success response with serialized data.
                return Response({'message': message, 'data': serializer.data}, status=status.HTTP_200_OK)
        else:
            if request.accepted_renderer.format == 'html':
                # For HTML requests with invalid data, render the template with error messages.
                context = {'serializer': serializer,
                       'vendor_instance': vendor_instance,
                       'remarks_list': self.get_remarks()}
                return render(request, self.template_name, context)
            else:
                # For API requests with invalid data, return an error response with serializer errors.
                return create_api_response(status_code=status.HTTP_400_BAD_REQUEST,
                                       message="We apologize for the inconvenience, but please review the below information.",
                                       data=convert_serializer_errors(serializer.errors))


            