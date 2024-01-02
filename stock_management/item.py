import pandas as pd
import xlwt
from django.shortcuts import render, redirect
from django.conf import settings
from django.http import HttpResponse
from infinity_fire_solutions.aws_helper import *
from infinity_fire_solutions.permission import *
from .models import *
from .item_serializers import *
from infinity_fire_solutions.response_schemas import *
from django.contrib import messages
from rest_framework import generics, status, filters
from rest_framework.renderers import TemplateHTMLRenderer, JSONRenderer
from rest_framework.views import APIView
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST
from django.template.response import TemplateResponse
from django.core.serializers import serialize
from drf_yasg.utils import swagger_auto_schema
from infinity_fire_solutions.utils import docs_schema_response_new


class ItemListView(CustomAuthenticationMixin,generics.CreateAPIView):
    """
    View to get the listing of all contacts.
    Supports both HTML and JSON response formats.
    """
    serializer_class = ItemSerializer
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']
    template_name = 'item_list.html'
    ordering_fields = ['created_at'] 

    common_get_response = {
    status.HTTP_200_OK: 
        docs_schema_response_new(
            status_code=status.HTTP_200_OK,
            serializer_class=serializer_class,
            message = "Data retrieved",
            )
    }
    
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

    def get_item_queryset(self):
         # Call the handle_unauthenticated method to handle unauthenticated access
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self, "stock_management", HasUpdateDataPermission, 'change'
        )
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect

        vendor_instance = self.get_queryset()
        if vendor_instance:
            # Define a mapping of data access values to corresponding filters
            filter_mapping = {
                "self": Q(user_id=self.request.user ),
                "all": Q(),  # An empty Q() object returns all data
            }

            # Get the appropriate filter from the mapping based on the data access value,
            # or use an empty Q() object if the value is not in the mapping
            queryset = Item.objects.filter(filter_mapping.get(data_access_value, Q())).order_by('-created_at')
            queryset = queryset.filter(vendor_id=vendor_instance )

        return queryset


    def get_item_instancee(self):
        item_data = Item.objects.filter(vendor_id=self.kwargs.get('vendor_id'),
                                        pk=self.kwargs.get('item_id')).first()
        return item_data


    @swagger_auto_schema(operation_id='Item Listing', responses={**common_get_response})
    def get(self, request, *args, **kwargs):
        """
        Handle both AJAX (JSON) and HTML requests.
        """
        # Call the handle_unauthenticated method to handle unauthenticated access
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self, "stock_management", HasUpdateDataPermission, 'change'
        )
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect

        vendor_id = self.kwargs.get('vendor_id')
        vendor_instance = self.get_queryset()
        if vendor_instance:
           
            if request.accepted_renderer.format == 'html':
                
                item_instance = self.get_item_instancee()
                if item_instance:
                    serializer = self.serializer_class(instance=item_instance)
                else:
                    serializer = self.serializer_class()
                
                context = {'item_list':self.get_item_queryset(),
                'vendor_instance':vendor_instance,
                'vendor_id':vendor_id,
                'serializer':serializer}
                return render_html_response(context,self.template_name)
        else:
            messages.error(request, "Item not found OR You are not authorized to perform this action.")
            return redirect(reverse('vendor_list'))

    def post(self, request, *args, **kwargs):
        """
        Handle POST request to add a item.
        """
        vendor_instance = self.get_queryset()
        if vendor_instance:
            item_instance = self.get_item_instancee()
            data = request.data
    
            file_list = data.get('file_list', [])
            
            if not any(file_list):
                data = data.copy()      # make a mutable copy of data before performing delete.
                del data['file_list']
            
            serializer_data = request.data if any(file_list) else data
            
            # Check if the site address instance exists for the customer
            if item_instance:
                # If the site address instance exists, update it.
                serializer = self.serializer_class(data=serializer_data, instance=item_instance, context={'request': request})
                message = "Item has been added successfully."
            else: 
                # If the site address instance does not exist, create a new one.
                serializer = self.serializer_class(data=serializer_data, context={'request': request})
                message = "Item has been updated successfully."

            if serializer.is_valid():
                if not item_instance:
                    serializer.validated_data['user_id'] = request.user 
                    serializer.validated_data['vendor_id'] = vendor_instance # Assign the current user instance.
                user = serializer.save()
                user.save()
                if request.accepted_renderer.format == 'html':
                    messages.success(request, message)
                    return redirect(reverse('item_list', kwargs={'vendor_id': kwargs['vendor_id']}))

            else:
                context = {
                    'item_list':self.get_item_queryset(),
                    'vendor_instance':vendor_instance,
                    'serializer':serializer}
                return render_html_response(context,self.template_name)
            
        else:
            messages.error(request, "Item not found OR You are not authorized to perform this action.")
            return redirect(reverse('vendor_list'))

class ItemAddView(CustomAuthenticationMixin, generics.CreateAPIView):
    """
    View for adding or updating a item.
    Supports both HTML and JSON response formats.
    """
    serializer_class = ItemSerializer
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'item_form.html'

    
    @swagger_auto_schema(auto_schema=None) 
    def get(self, request, *args, **kwargs):
        """
        Handle GET request to display a form for updating a item.
        If the item exists, retrieve the serialized data and render the HTML template.
        If the item does not exist, render the HTML template with an empty serializer.
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
                message = "Item has been added successfully.",
                ),
        status.HTTP_400_BAD_REQUEST: 
            docs_schema_response_new(
                status_code=status.HTTP_400_BAD_REQUEST,
                serializer_class=serializer_class,
                message = "We apologize for the inconvenience, but please review the below information.",
                ),

    }  

    @swagger_auto_schema(operation_id='Add Item', responses={**common_post_response})
    def post(self, request, *args, **kwargs):
        """
        Handle POST request to add a item.
        """
        message = "Item has been added successfully."
        
        data = request.data
        # Retrieve the 'file_list' key from the copied data, or use None if it doesn't exist
        file_list = data.get('file_list', None)

        if file_list is not None and not any(file_list):
            data = data.copy()
            del data['file_list']  # Remove the 'file_list' key if it's a blank list or None
            
        serializer = self.serializer_class(data=data)

        if serializer.is_valid():
            serializer.validated_data['user_id'] = request.user  # Assign the current user instance.
            user = serializer.save()
            user.save()
            if request.accepted_renderer.format == 'html':
                messages.success(request, message)
                return redirect(reverse('item_list'))

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

class ItemUpdateView(CustomAuthenticationMixin, generics.UpdateAPIView):
    """
    API view for updating a Item.

    This view handles both HTML and API requests for updating a Item instance.
    If the Item instance exists, it will be updated with the provided data.
    Otherwise, an error message will be returned.

    The following request methods are supported:
    - POST: Updates the Item instance.

    Note: Make sure to replace 'your_template_name.html' with the appropriate HTML template name.
    """
    
    serializer_class = ItemSerializer
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'item_form.html'
    def get_queryset(self):
        """
        Get the queryset for listing Item items.

        Returns:
            QuerySet: A queryset of Item items filtered based on the authenticated user's ID.
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

        queryset = Item.objects.filter(filter_mapping.get(data_access_value, Q()))

        # Filter the queryset based on the provided 'item_id'
        instance = queryset.filter(pk= self.kwargs.get('item_id')).first()
        return instance

    @swagger_auto_schema(auto_schema=None) 
    def get(self, request, *args, **kwargs):
        # This method handles GET requests for updating an existing item_list object.
        if request.accepted_renderer.format == 'html':
            instance = self.get_queryset()
            if instance:
                serializer = self.serializer_class(instance=instance, context={'request': request})
                context = {'serializer': serializer, 'item_instance': instance}
                return render_html_response(context, self.template_name)
            else:
                messages.error(request, "You are not authorized to perform this action")
                return redirect(reverse('item_list'))
            
    common_put_response = {
        status.HTTP_200_OK: 
            docs_schema_response_new(
                status_code=status.HTTP_200_OK,
                serializer_class=serializer_class,
                message = "Item has been updated successfully!",
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

    @swagger_auto_schema(operation_id='Edit Item', responses={**common_put_response})
    def post(self, request, *args, **kwargs):
        """
        Handle POST request to update a Item instance.

        Args:
            request (rest_framework.request.Request): The HTTP request object.
            *args: Variable-length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            rest_framework.response.Response: HTTP response object.
                If successful, the Item is updated, and the appropriate response is returned.
                If unsuccessful, an error response is returned.
        """

        data = request.data
        # Retrieve the 'file_list' key from the copied data, or use None if it doesn't exist
        file_list = data.get('file_list', None)

        if file_list is not None and not any(file_list):
            data = data.copy()
            del data['file_list']  # Remove the 'file_list' key if it's a blank list or None
        
        instance = self.get_queryset()
        if instance:
            data = request.data
            # Retrieve the 'file_list' key from the copied data, or use None if it doesn't exist
            file_list = data.get('file_list', None)

            if file_list is not None and not any(file_list):
                data = data.copy()
                del data['file_list']  # Remove the 'file_list' key if it's a blank list or None
                serializer = self.serializer_class(data = data)
            else:
                serializer = self.serializer_class(instance=instance, data=request.data, context={'request': request})
            
            if serializer.is_valid():
                # If the serializer data is valid, save the updated Item instance.
                serializer.update(instance, validated_data=serializer.validated_data)
                message = "Item has been updated successfully!"

                if request.accepted_renderer.format == 'html':
                    # For HTML requests, display a success message and redirect to item_list.
                    messages.success(request, message)
                    return redirect(reverse('item_list'))
                else:
                    # For API requests, return a success response with serialized data.
                    return Response({'message': message, 'data': serializer.data}, status=status.HTTP_200_OK)
            else:
                if request.accepted_renderer.format == 'html':
                    # For HTML requests with invalid data, render the template with error messages.
                    context = {'serializer': serializer, 'item_instance': instance}
                    return render(request, self.template_name, context)
                else:
                    # For API requests with invalid data, return an error response with serializer errors.
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            error_message = "You are not authorized to perform this action"
            if request.accepted_renderer.format == 'html':
                # For HTML requests with no instance, display an error message and redirect to item_list.
                messages.error(request, error_message)
                return redirect('item_list')
            else:
                # For API requests with no instance, return an error response with an error message.
                return Response({'message': error_message}, status=status.HTTP_400_BAD_REQUEST)
            
class ItemDeleteView(CustomAuthenticationMixin, generics.DestroyAPIView):
    """
    View for deleteing .
    Supports both HTML and JSON response formats.
    """
    serializer_class = ItemSerializer
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]


    common_delete_response = {
        status.HTTP_200_OK: 
            docs_schema_response_new(
                status_code=status.HTTP_200_OK,
                serializer_class=serializer_class,
                message = "Item has been deleted successfully!",
                ),
        status.HTTP_404_NOT_FOUND: 
            docs_schema_response_new(
                status_code=status.HTTP_404_NOT_FOUND,
                serializer_class=serializer_class,
                message = "Item not found OR You are not authorized to perform this action.",
                ),

    }
    @swagger_auto_schema(operation_id='Delete Item', responses={**common_delete_response})
    def delete(self, request, *args, **kwargs):
        """
        Handle DELETE request to delete a item.
        """
        # Get the item instance from the database
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

        queryset = Item.objects.filter(filter_mapping.get(data_access_value, Q()))
        item = queryset.filter(pk= self.kwargs.get('item_id')).first()

        if item:
            images = ItemImage.objects.filter(item_id=item)
            # Proceed with the deletion
            # check if any image on s3
            for image in images:
                if image.image_path:
                    s3_client.delete_object(Bucket=settings.AWS_BUCKET_NAME, Key=item.image_path)
                    image.delete()

            item.delete()
            messages.success(request, "Item has been deleted successfully!")
            return create_api_response(status_code=status.HTTP_404_NOT_FOUND,
                                        message="Item has been deleted successfully!", )
        else:
            messages.error(request, "Item not found OR You are not authorized to perform this action.")
            return create_api_response(status_code=status.HTTP_404_NOT_FOUND,
                                        message="Item not found OR You are not authorized to perform this action.", )

class ItemRemoveImageView(generics.DestroyAPIView):
    """
    View to remove a document associated with item.
    """
    swagger_schema = None
    
    def destroy(self, request, *args, **kwargs):
        """
        Handles DELETE request to remove the document associated with a item.
        """
        item_id = kwargs.get('item_id')
        if item_id:
            image_instance = ItemImage.objects.filter(item_id=item_id, pk=kwargs.get('pk') ).get()
            if image_instance and image_instance.image_path: 
                
                s3_client.delete_object(Bucket=settings.AWS_BUCKET_NAME, Key = image_instance.image_path)
                image_instance.delete()
            return Response(
                {"message": "Your item image has been deleted successfully."},
                status=status.HTTP_204_NO_CONTENT
            )
        else:
            return Response(
                {"message": "Requirement Defect not found or you don't have permission to delete."},
                status=status.HTTP_404_NOT_FOUND
            )
        

class ItemDetailView(CustomAuthenticationMixin, generics.RetrieveAPIView):
    """
    API view for View a Item.

    This view handles both HTML and API requests for updating a Item instance.
    If the Item instance exists, it will be updated with the provided data.
    Otherwise, an error message will be returned.

    The following request methods are supported:
    - POST: Updates the Item instance.

    Note: Make sure to replace 'your_template_name.html' with the appropriate HTML template name.
    """
    
    serializer_class = ItemSerializer
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'item_detail.html'

    def get_queryset(self):
        """
        Get the queryset for listing vendor items.

        Returns:
            QuerySet: A queryset of vendor items filtered based on the authenticated user's ID.
        """
        # Get the model class using the provided module_name string
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self, "stock_management", HasUpdateDataPermission, 'view'
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

    def get_item_queryset(self):
         # Call the handle_unauthenticated method to handle unauthenticated access
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self, "stock_management", HasUpdateDataPermission, 'view'
        )
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect

        vendor_instance = self.get_queryset()
        if vendor_instance:
            # Define a mapping of data access values to corresponding filters
            filter_mapping = {
                "self": Q(user_id=self.request.user ),
                "all": Q(),  # An empty Q() object returns all data
            }

            # Get the appropriate filter from the mapping based on the data access value,
            # or use an empty Q() object if the value is not in the mapping
            queryset = Item.objects.filter(filter_mapping.get(data_access_value, Q())).order_by('-created_at')
            queryset = queryset.filter(vendor_id=vendor_instance )

        return queryset


    def get_item_instancee(self):
        item_data = Item.objects.filter(vendor_id=self.kwargs.get('vendor_id'),
                                        pk=self.kwargs.get('item_id')).first()
        return item_data


   
    def get(self, request, *args, **kwargs):
        """
        Handle both AJAX (JSON) and HTML requests.
        """
        # Call the handle_unauthenticated method to handle unauthenticated access
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self, "stock_management", HasUpdateDataPermission, 'view'
        )
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect
        vendor_id = self.kwargs.get('vendor_id')
        vendor_instance = self.get_queryset()
        if vendor_instance:
           
            if request.accepted_renderer.format == 'html':
                
                item_instance = self.get_item_instancee()
                if item_instance:
                    serializer = self.serializer_class(instance=item_instance)
                else:
                    serializer = self.serializer_class()
                
                context = {'item_list':self.get_item_queryset(),
                'vendor_instance':vendor_instance,
                'serializer':serializer,
                    'vendor_id':vendor_id}
                return render_html_response(context,self.template_name)
        else:
            messages.error(request, "Item not found OR You are not authorized to perform this action.")
            return redirect(reverse('vendor_list'))
        
class ItemExcelDownloadAPIView(APIView):
    def get(self, request, *args, **kwargs):
        # Get your item queryset based on your requirements
        items = Item.objects.filter(vendor_id=self.kwargs.get('vendor_id'))

        # Create a new workbook and add a worksheet.
        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet('Item Details')

        # Write the headers
        headers = ["Item Name", "Description", "Category", "Price", "Units", "Quantity Per Box", "Reference Number"]
        for col_num, header in enumerate(headers):
            worksheet.write(0, col_num, header)

        # Write the data
        for row_num, item in enumerate(items, start=1):
            worksheet.write(row_num, 0, item.item_name)
            worksheet.write(row_num, 1, item.description)
            worksheet.write(row_num, 2, item.category_id.name)
            worksheet.write(row_num, 3, item.price)
            worksheet.write(row_num, 4, item.units)
            worksheet.write(row_num, 5, item.quantity_per_box)
            worksheet.write(row_num, 6, item.reference_number)

        # Create a response with the Excel file
        response = HttpResponse(content_type='application/ms-excel')
        response['Content-Disposition'] = 'attachment; filename="item_details.xls"'
        workbook.save(response)
        return response

class UploadExcelView(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'upload_file.html'
    serializer_class = ItemUploadSerializer

    def get(self, request, *args, **kwargs):
        serializer = self.serializer_class()
        return TemplateResponse(request, self.template_name, {'serializer': serializer})

    def post(self, request, *args, **kwargs):
        uploaded_file = request.FILES.get('excel_file')

        if not uploaded_file:
            return Response({'error': 'No file uploaded'}, status=HTTP_400_BAD_REQUEST)

        try:
            excel_data = pd.read_excel(uploaded_file)
        except pd.errors.ParserError:
            return Response({'error': 'Invalid Excel file format'}, status=HTTP_400_BAD_REQUEST)

        column_names = list(excel_data.columns)
        system_attributes = column_names

        serializer = self.serializer_class(data=excel_data.to_dict(orient='records'), many=True)

        if not serializer.is_valid():
            return Response({'error': 'Invalid data from Excel file'}, status=HTTP_400_BAD_REQUEST)

        serialized_data = serializer.data
        mapping = request.data.get('mapping', {})

        for index, row in excel_data.iterrows():
            vendor_stock_data = {}

            for excel_column, system_attribute in mapping.items():
                vendor_stock_data[system_attribute] = row[excel_column]

            # Create or update Vendor Stock items based on vendor_stock_data
            # Example:
            # VendorStock.objects.update_or_create(**vendor_stock_data)

        # Retrieve vendor_id from request's query parameters
        vendor_id = request.query_params.get('vendor_id')

        if vendor_id is None:
            return Response({'error': 'Vendor ID is missing in the request'}, status=HTTP_400_BAD_REQUEST)

        # Redirect to the item listing page after processing
        return redirect(reverse('item_list', kwargs={'vendor_id': vendor_id}))

        context = {'message': 'Upload successful', 'excel_data': excel_data, 'mapping': mapping, 'serialized_data': serialized_data}
        return TemplateResponse(request, self.template_name, context)