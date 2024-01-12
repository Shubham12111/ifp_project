from io import BytesIO
from django.shortcuts import render, redirect
from django.conf import settings
from django.http import Http404
from infinity_fire_solutions.aws_helper import *
from infinity_fire_solutions.permission import *
from requirement_management.models import *
from .serializers import *
from requirement_management.views import get_customer_data
from infinity_fire_solutions.response_schemas import *
from django.contrib import messages
from rest_framework import generics, status, filters
from rest_framework.renderers import TemplateHTMLRenderer, JSONRenderer
from drf_yasg.utils import swagger_auto_schema
from infinity_fire_solutions.utils import docs_schema_response_new
import pandas as pd
from common_app.models import UpdateWindowConfiguration
from django.db import transaction

from requirement_management.serializers import RequirementCustomerSerializer


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



class CSSORCustomerListView(CustomAuthenticationMixin,generics.ListAPIView):
    
    serializer_class = RequirementCustomerSerializer
    renderer_classes = [TemplateHTMLRenderer,JSONRenderer]
    filter_backends = [filters.SearchFilter]
    search_fields = ['customer_id__first_name', 'customer_id__last_name']
    template_name = 'sor/sor_customer_list.html'
    ordering_fields = ['created_at'] 

    def get_queryset(self):
            queryset = User.objects.filter(is_active=True,  roles__name__icontains='customer').exclude(pk=self.request.user.id)
            return queryset

    def get(self, request, *args, **kwargs):
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self, "customer", HasListDataPermission, 'list'
        )
        
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect

        queryset = self.get_queryset()
        all_sor = SORItem.objects.filter()

        customers_with_counts = []  # Create a list to store customer objects with counts

        for customer in queryset:
            sor_counts = all_sor.filter(customer_id=customer).count()
            customers_with_counts.append({'customer': customer, 'sor_counts': sor_counts})

        if request.accepted_renderer.format == 'html':
            context = {'customers_with_counts': customers_with_counts}  # Pass the list of customers with counts to the template
            return render_html_response(context, self.template_name)
        else:
            serializer = self.serializer_class(queryset, many=True)
            return create_api_response(status_code=status.HTTP_200_OK,
                                    message="Data retrieved",
                                    data=serializer.data)

class CSSORListView(CustomAuthenticationMixin, generics.ListAPIView):
    """
    View to get the listing of Service Order Requests (SOR).
    Supports both HTML and JSON response formats.
    """
    
    serializer_class = SORSerializer
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']
    template_name = 'sor_list.html'
    ordering_fields = ['-created_at']

    common_get_response = {
        status.HTTP_200_OK: docs_schema_response_new(
            status_code=status.HTTP_200_OK,
            serializer_class=serializer_class,
            message="Data retrieved",
        )
    }
    @swagger_auto_schema(operation_id='SOR Listing', responses={**common_get_response})
    def get(self, request, *args, **kwargs):
        """
        Handle both AJAX (JSON) and HTML requests for listing SOR items.
        """
        
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self, "customer", HasListDataPermission, 'list'
        )

        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect

        # Define a mapping of data access values to corresponding filters
        filter_mapping = {
            "self": Q(user_id=request.user),
            "all": Q(),  # An empty Q() object returns all data
        }

        # Get the appropriate filter from the mapping based on the data access value,
        # or use an empty Q() object if the value is not in the mapping
        data_access_filter = filter_mapping.get(data_access_value, Q())

        customer_id = kwargs.get('customer_id')

        customer_data = get_customer_data(customer_id)
        # Get the active update window
        update_window = UpdateWindowConfiguration.objects.filter(is_active=True).first()
        if customer_data:
            # Apply filters and retrieve SOR items for the specified customer
            sor_queryset = SORItem.objects.filter(data_access_filter, customer_id=customer_data).order_by('-created_at')
            if request.accepted_renderer.format == 'html':
                serializer = self.serializer_class()
                context = {'list_sor': sor_queryset, 'customer_id':customer_id,'customer_instance': customer_data,'update_window': update_window,'serializer': serializer}
                return render_html_response(context, self.template_name)
            else:
                serializer = self.serializer_class(sor_queryset, many=True)
                return create_api_response(
                    status_code=status.HTTP_200_OK,
                    message="Data retrieved",
                    data=serializer.data
                )
        else:
            messages.error(request, "You are not authorized to perform this action")
            return redirect(reverse('cs_sor_customers_list'))



class CSSORAddView(CustomAuthenticationMixin, generics.CreateAPIView):
    """
    View for adding or updating a SOR.
    Supports both HTML and JSON response formats.
    """
    serializer_class = SORSerializer
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'sor_list.html'

    def get_sor_list(self, request, customer_id):
        """
        Handle both AJAX (JSON) and HTML requests for listing SOR items.
        """
        
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self, "customer", HasListDataPermission, 'list'
        )

        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect

        # Define a mapping of data access values to corresponding filters
        filter_mapping = {
            "self": Q(user_id=request.user),
            "all": Q(),  # An empty Q() object returns all data
        }

        # Get the appropriate filter from the mapping based on the data access value,
        # or use an empty Q() object if the value is not in the mapping
        data_access_filter = filter_mapping.get(data_access_value, Q())
        # Get the active update window
        sor_queryset = SORItem.objects.filter(data_access_filter, customer_id=customer_id).order_by('-created_at')

        return sor_queryset

    @swagger_auto_schema(auto_schema=None) 
    def get(self, request, *args, **kwargs):
        """
        Handle GET request to display a form for updating a SOR.
        If the SOR exists, retrieve the serialized data and render the HTML template.
        If the SOR does not exist, render the HTML template with an empty serializer.
        """
        # Call the handle_unauthenticated method to handle unauthenticated access
        authenticated_user, data_access_value = check_authentication_and_permissions(
           self,"customer", HasCreateDataPermission, 'add'
        )
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect

        customer_id = kwargs.get('customer_id')
        
        customer_data = get_customer_data(customer_id)
        # Apply an additional filter for customer_id
        if customer_data:
            
            if request.accepted_renderer.format == 'html':
                context = {'serializer':self.serializer_class(), 'customer_id': customer_id}
                return render_html_response(context,self.template_name)
            else:
                return create_api_response(status_code=status.HTTP_201_CREATED,
                                    message="GET Method Not Alloweded",)
        
        else:
            messages.error(request, "You are not authorized to perform this action")
            return redirect(reverse('cs_sor_customers_list', kwargs={'customer_id': customer_id}))
        
        
    common_post_response = {
        status.HTTP_200_OK: 
            docs_schema_response_new(
                status_code=status.HTTP_200_OK,
                serializer_class=serializer_class,
                message = "SOR has been added successfully.",
                ),
        status.HTTP_400_BAD_REQUEST: 
            docs_schema_response_new(
                status_code=status.HTTP_400_BAD_REQUEST,
                serializer_class=serializer_class,
                message = "We apologize for the inconvenience, but please review the below information.",
                ),

    }  

    @swagger_auto_schema(operation_id='Add SOR', responses={**common_post_response})
    def post(self, request, *args, **kwargs):
        """
        Handle POST request to add a SOR.
        """

        customer_id = kwargs.get('customer_id')
        
        customer_data = get_customer_data(customer_id)

        # Check if the user is authorized to perform this action
        if not customer_data:
            messages.error(request, "You are not authorized to perform this action")
            return redirect(reverse('cs_sor_customers_list', kwargs={'customer_id': customer_id}))

        data = request.data
        file_list = data.getlist('file_list', None)

        if file_list is not None and not any(file_list):
            data = data.copy()
            del data['file_list']  # Remove the 'file_list' key if it's a blank list or None

        update_window = UpdateWindowConfiguration.objects.filter(is_active=True).first()

        # Retrieve existing SOR codes for the current customer
        existing_sor_codes = SORItem.objects.filter(customer_id=customer_id).values_list('reference_number', flat=True)

        # Create a serializer instance with the data and the queryset for reference_number uniqueness check
        serializer = self.serializer_class(data=data)

        if serializer.is_valid():
            # Check if the reference_number is unique for the current customer
            if serializer.validated_data['reference_number'] in existing_sor_codes:
                messages.error(request, "This SOR code is already in use for this customer.")
                return redirect(reverse('cs_customer_sor_list', kwargs={'customer_id': kwargs.get('customer_id')}))

            # Assign additional data to the serializer before saving
            serializer.validated_data['customer_id'] = User.objects.get(pk=kwargs.get('customer_id'))
            serializer.validated_data['user_id'] = request.user

            serializer.save()

            if update_window:
                message = f"SOR has been added successfully. You can update SOR till {update_window.end_date}."
            else:
                message = "SOR has been added successfully."

            if request.accepted_renderer.format == 'html':
                messages.success(request, message)
                return redirect(reverse('cs_customer_sor_list', kwargs={'customer_id': kwargs.get('customer_id')}))
            else:
                # Return JSON response with success message and serialized data
                return create_api_response(
                    status_code=status.HTTP_201_CREATED,
                    message=message,
                    data=serializer.data
                )
        else:
            # Invalid serializer data
            if request.accepted_renderer.format == 'html':
                # Render the HTML template with invalid serializer data
                context = {'list_sor': self.get_sor_list(request, customer_id), 
                           'customer_id': customer_id,
                           'serializer': serializer,
                           'customer_instance': customer_data
                           }
                return render_html_response(context, self.template_name)
            else:
                # Return JSON response with error message
                return create_api_response(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    message="We apologize for the inconvenience, but please review the below information."
                )

   
        
        
class CSSORUpdateView(CustomAuthenticationMixin, generics.UpdateAPIView):
    """
    API view for updating a SOR.

    This view handles both HTML and API requests for updating a SOR instance.
    If the SOR instance exists, it will be updated with the provided data.
    Otherwise, an error message will be returned.

    The following request methods are supported:
    - POST: Updates the SOR instance.

    Note: Make sure to replace 'your_template_name.html' with the appropriate HTML template name.
    """
    
    serializer_class = SORSerializer
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'sor_list.html'


    def get_sor_list(self, request, customer_id):
        """
        Handle both AJAX (JSON) and HTML requests for listing SOR items.
        """
        
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self, "customer", HasListDataPermission, 'list'
        )

        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect

        # Define a mapping of data access values to corresponding filters
        filter_mapping = {
            "self": Q(user_id=request.user),
            "all": Q(),  # An empty Q() object returns all data
        }

        # Get the appropriate filter from the mapping based on the data access value,
        # or use an empty Q() object if the value is not in the mapping
        data_access_filter = filter_mapping.get(data_access_value, Q())
        # Get the active update window
        sor_queryset = SORItem.objects.filter(data_access_filter, customer_id=customer_id).order_by('-created_at')

        return sor_queryset
    

    def get_queryset(self):
        """
        Get the queryset for listing SOR SORs.

        Returns:
            QuerySet: A queryset of SOR SORs filtered based on the authenticated user's ID.
        """
        
        # Get the model class using the provided module_name string
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self, "customer", HasUpdateDataPermission, 'change'
        )

        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect

        # Define a mapping of data access values to corresponding filters
        filter_mapping = {
            "self": Q(user_id=self.request.user ),
            "all": Q(),  # An empty Q() object returns all data
        }

        queryset = SORItem.objects.filter(filter_mapping.get(data_access_value, Q()))

        # Filter the queryset based on the provided 'SOR_id'
        instance = queryset.filter(pk= self.kwargs.get('sor_id')).first()
        return instance

    @swagger_auto_schema(auto_schema=None) 
    def get(self, request, *args, **kwargs):
        customer_id = kwargs.get('customer_id')
        customer_data = get_customer_data(customer_id)
        
        # Apply an additional filter for customer_id
        if customer_data:
            # This method handles GET requests for updating an existing list_sor object.
            if request.accepted_renderer.format == 'html':
                instance = self.get_queryset()
                if instance:
                    serializer = self.serializer_class(instance=instance, context={'request': request})
                   
                    context = {'serializer': serializer, 'sor_instance': instance, 'customer_id': customer_id,
                               'list_sor': self.get_sor_list(request, customer_id), 'customer_instance':customer_data}
                    return render_html_response(context, self.template_name)
                else:
                    messages.error(request, "You are not authorized to perform this action")
                    return redirect(reverse('cs_customer_sor_list', kwargs={'customer_id': kwargs.get('customer_id')}))
        else:
            messages.error(request, "You are not authorized to perform this action")
            return redirect(reverse('cs_customer_sor_list', kwargs={'customer_id': kwargs.get('customer_id')}))
            
    common_put_response = {
        status.HTTP_200_OK: 
            docs_schema_response_new(
                status_code=status.HTTP_200_OK,
                serializer_class=serializer_class,
                message = "SOR has been updated successfully!",
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

    @swagger_auto_schema(operation_id='Edit SOR', responses={**common_put_response})
    def post(self, request, *args, **kwargs):
        """
        Handle POST request to update a SOR instance.

        Args:
            request (rest_framework.request.Request): The HTTP request object.
            *args: Variable-length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            rest_framework.response.Response: HTTP response object.
                If successful, the SOR is updated, and the appropriate response is returned.
                If unsuccessful, an error response is returned.
        """
        customer_id = kwargs.get('customer_id')
        customer_data = get_customer_data(customer_id)
        
        # Apply an additional filter for customer_id
        if customer_data:
            data = request.data
            # Retrieve the 'file_list' key from the copied data, or use None if it doesn't exist
            file_list = data.getlist('file_list', None)

            if file_list is not None and not any(file_list):
                data = data.copy()
                del data['file_list']  # Remove the 'file_list' key if it's a blank list or None

            instance = self.get_queryset()
            if instance:
                
                serializer = self.serializer_class(instance=instance, data=data, context={'request': request})

                if serializer.is_valid():
                    # If the serializer data is valid, save the updated SOR instance.
                    serializer.save()
                    message = "SOR has been updated successfully!"

                    if request.accepted_renderer.format == 'html':
                        # For HTML requests, display a success message and redirect to list_sor.
                        messages.success(request, message)
                        return redirect(reverse('cs_customer_sor_list', kwargs={'customer_id': kwargs.get('customer_id')}))
                    else:
                        # For API requests, return a success response with serialized data.
                        return Response({'message': message, 'data': serializer.data}, status=status.HTTP_200_OK)
                else:
                    if request.accepted_renderer.format == 'html':
                        # For HTML requests with invalid data, render the template with error messages.
                        context = {'serializer': serializer, 'sor_instance': instance, 'customer_id': customer_id}
                        return render(request, self.template_name, context)
                    else:
                        # For API requests with invalid data, return an error response with serializer errors.
                        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                
                
            else:
                error_message = "You are not authorized to perform this action"
                if request.accepted_renderer.format == 'html':
                    # For HTML requests with no instance, display an error message and redirect to list_sor.
                    messages.error(request, error_message)
                    return redirect(reverse('cs_customer_sor_list', kwargs={'customer_id': kwargs.get('customer_id')}))
                else:
                    # For API requests with no instance, return an error response with an error message.
                    return Response({'message': error_message}, status=status.HTTP_400_BAD_REQUEST)
        else:
            messages.error(request, "You are not authorized to perform this action")
            return redirect(reverse('cs_sor_customers_list', kwargs={'customer_id': customer_id}))

        
class CSSORDeleteView(CustomAuthenticationMixin, generics.DestroyAPIView):
    """
    View for deleteing .
    Supports both HTML and JSON response formats.
    """
    serializer_class = SORSerializer
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]


    common_delete_response = {
        status.HTTP_200_OK: 
            docs_schema_response_new(
                status_code=status.HTTP_200_OK,
                serializer_class=serializer_class,
                message = "SOR has been deleted successfully!",
                ),
        status.HTTP_404_NOT_FOUND: 
            docs_schema_response_new(
                status_code=status.HTTP_404_NOT_FOUND,
                serializer_class=serializer_class,
                message = "SOR not found OR You are not authorized to perform this action.",
                ),

    }
    @swagger_auto_schema(operation_id='Delete SOR', responses={**common_delete_response})
    def delete(self, request, *args, **kwargs):
        """
        Handle DELETE request to delete a SOR.
        """
        # Get the SOR instance from the database
        # Call the handle_unauthenticated method to handle unauthenticated access

        authenticated_user, data_access_value = check_authentication_and_permissions(
            self,"customer", HasDeleteDataPermission, 'delete'
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

        queryset = SORItem.objects.filter(filter_mapping.get(data_access_value, Q()))
        sor_obj = queryset.filter(pk= self.kwargs.get('sor_id')).first()

        if sor_obj:
            images = SORItemImage.objects.filter(sor_id=sor_obj)
            # Proceed with the deletion
            # check if any image on s3
            for image in images:
                if image.image_path:
                    s3_client.delete_object(Bucket=settings.AWS_BUCKET_NAME, Key=image.image_path)
                    image.delete()

            sor_obj.delete()
            messages.success(request, "SOR has been deleted successfully!")
            return create_api_response(status_code=status.HTTP_404_NOT_FOUND,
                                        message="SOR has been deleted successfully!", )
        else:
            messages.error(request, "SOR not found OR You are not authorized to perform this action.")
            return create_api_response(status_code=status.HTTP_404_NOT_FOUND,
                                        message="SOR not found OR You are not authorized to perform this action.", )
        
class CSSORDetailView(generics.RetrieveAPIView):
    """
    API view for retrieving the details of a Single Object Request (SOR).

    This view handles both HTML and API requests for retrieving SOR details.
    """
    serializer_class = SORSerializer
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'sor/sor_detail.html'

    def get_queryset(self):
        """
        Get the queryset for retrieving a SOR instance.

        Returns:
            QuerySet: A queryset of SOR instances filtered based on the authenticated user's ID.
        """
        # Implement your logic to filter SOR instances based on user permissions and data access.

    def get_queryset(self):
        """
        Get the queryset for retrieving a SOR instance.

        Returns:
            QuerySet: A queryset of SOR instances filtered based on the authenticated user's ID.
        """
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self, "customer", HasUpdateDataPermission, 'change'
        )

        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect

        # Define a mapping of data access values to corresponding filters
        filter_mapping = {
            "self": Q(user_id=self.request.user),
            "all": Q(),  # An empty Q() object returns all data
        }

        queryset = SORItem.objects.filter(filter_mapping.get(data_access_value, Q()))

        return queryset  # Make sure to return the queryset

    def get_object(self):
        """
        Get the SOR instance.

        Returns:
            SORItem: A single SOR instance.
        """
        try:
            sor_id = self.kwargs.get('sor_id')
            return SORItem.objects.get(pk=sor_id)
        except SORItem.DoesNotExist:
            raise Http404("SOR not found")

    def get(self, request, *args, **kwargs):
        # Get the SOR instance
        customer_id = kwargs.get('customer_id')
        instance = self.get_object()

        if instance:
            if request.accepted_renderer.format == 'html':
                # For HTML requests, render the template with the SOR instance
                serializer = self.serializer_class(instance=instance, context={'request': request})
                context = {'serializer': serializer, 'sor_instance': instance,'customer_id': customer_id}
                return render(request, self.template_name, context)
            else:
                # For API requests, return a serialized SOR instance
                serializer = self.serializer_class(instance=instance)
                return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            messages.error(request, "SOR not found")
            return redirect(reverse('sor_list'))  # Redirect to a SOR list view or other appropriate page





class CSSORCSVView(CustomAuthenticationMixin, generics.CreateAPIView):
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'sor_list.html'
    serializer_class = SORSerializer
    EXCEL = ['xlsx', 'xls', 'ods']
    CSV = ['csv']

    default_fieldset = ['SOR code', 'Trade', 'Full Description', 'Unit of Measure', 'Price','Category id']

    def get_file_ext(self, file_name: str) -> str:
        ext = file_name.split('.')[-1].lower()
        return ext

    def get_excel_engine(self, file_ext: str) -> str or None:
        engines = {'xlsx': 'openpyxl', 'xls': 'xlrd', 'ods': 'odf'}
        return engines[file_ext]

    def read_file_to_df(self, file) -> pd.DataFrame:
        try:
            ext = self.get_file_ext(file.name)

            # Convert the in-memory file to a BytesIO object
            content = BytesIO(file.read())

            if ext in self.EXCEL:
                engine = self.get_excel_engine(ext)
                data_frame = pd.read_excel(content, engine=engine)
                return data_frame

            if ext in self.CSV:
                data_frame = pd.read_csv(content)
                return data_frame

            raise ValueError('The file type is not supported.')

        except Exception as e:
           
            return None
    
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        customer_id = kwargs.get('customer_id', None)
     
        # Check if the 'csv_file' key is present in the request.FILES dictionary
        csv_file = request.FILES.get('csv_file', None)
        if csv_file is None:
            return JsonResponse({'error': 'No file provided for upload.'}, status=400)

        try:
            # Read the CSV file into a DataFrame
            df = self.read_file_to_df(csv_file)
           
            if df is None:
                messages.error(request,'File format not supported.')
                return redirect(reverse('cs_customer_sor_list', kwargs={'customer_id': kwargs.get('customer_id')}))


            customer_data = get_customer_data(customer_id)
            if customer_data:
                # Map specific columns to serializer fields
                mapped_data = {
                    'reference_number': df['SOR code'],
                    'name': df['Trade'],
                    'description': df['Full Description'],
                    'units': df['Unit of Measure'],
                    'price': df['Price'],
                    'category_id':df['Category id'],
                }

                # Create a DataFrame from the mapped data
                mapped_df = pd.DataFrame(mapped_data)

                # Validate the mapped DataFrame against the serializer
                serializer = self.serializer_class(
                    data=mapped_df.to_dict(orient='records'),
                    many=True,
                    context={'request': request, 'customer_id': kwargs['customer_id']}
                )
                
                if serializer.is_valid():
                    # Save the data if validation passes
                    remove_data=SORItem.objects.filter(customer_id=customer_id)
                    remove_data.delete()
                    serializer.save(customer_id=customer_data)
                    messages.success(request, 'Bulk Sor uploaded successfully.')
                    if request.accepted_renderer.format == 'html':
                        return redirect(reverse('cs_customer_sor_list', kwargs={'customer_id': kwargs.get('customer_id')}))
                    else:
                        return create_api_response(
                            status_code=status.HTTP_200_OK,
                            message="Data retrieved",
                            data=serializer.data
                        )
                else:
                    if request.accepted_renderer.format == 'html':
                        messages.error(request, 'The file contains irrelavent data, please check data and try again')
                        return redirect(reverse('cs_customer_sor_list', kwargs={'customer_id': kwargs.get('customer_id')}))
                    else:
                        return JsonResponse({'error': 'Error validating data. Please check the file format and try again.',
                                            'validation_errors': serializer.errors}, status=400)
        except Exception as e:
            messages.error(request, 'The file contains irrelavent data, please check data and try again')
            return redirect(reverse('cs_customer_sor_list', kwargs={'customer_id': kwargs.get('customer_id')}))
           
        
    

class CSSORRemoveImageView(generics.DestroyAPIView):
    """
    View to remove a document associated with a sor.
    """
    swagger_schema = None
    
    def destroy(self, request, *args, **kwargs):
        """
        Handles DELETE request to remove the document associated with a sor.
        """
        sor_id = kwargs.get('sor_id')
        if sor_id:
            sor_instance = SORItemImage.objects.filter(sor_id=sor_id, pk=kwargs.get('pk') ).get()
            if sor_instance and sor_instance.image_path: 
                
                s3_client.delete_object(Bucket=settings.AWS_BUCKET_NAME, Key = sor_instance.image_path)
                sor_instance.delete()
            return Response(
                {"message": "Your Sor Document has been deleted successfully."},
                status=status.HTTP_204_NO_CONTENT
            )
        else:
            return Response(
                {"message": "Sor Document not found OR you don't have permission to delete."},
                status=status.HTTP_404_NOT_FOUND
            )