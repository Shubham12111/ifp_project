"""
This module contains views and utilities for managing purchase orders and related data.

It includes views for creating, updating, and deleting purchase orders, as well as retrieving and displaying
purchase order invoices. The module also provides utilities for generating purchase order numbers and handling
purchase order item data.

The module imports various modules and packages, including Django, DRF, and custom modules such as
`aws_helper`, `permission`, and `response_schemas`. It also uses models and serializers from the `stock_management`
app to handle vendor, inventory location, and item-related data.

"""

from django.http import HttpResponseRedirect
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status, filters
from rest_framework.renderers import TemplateHTMLRenderer, JSONRenderer
from django.contrib import messages
from infinity_fire_solutions.aws_helper import *
from infinity_fire_solutions.permission import *
from infinity_fire_solutions.response_schemas import create_api_response, render_html_response
from infinity_fire_solutions.utils import docs_schema_response_new
from stock_management.models import Vendor, InventoryLocation, Item
from stock_management.serializers import VendorSerializer
from .serializers import *
from .models import *
from stock_management.models import Item
from django.http import JsonResponse
from django.core import serializers
from django.views import View
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db import transaction
from datetime import datetime
from django.db.models import Sum
from django.db.models import F
from stock_management.models import Inventory
import json
from rest_framework.response import Response
from common_app.models import *
from customer_management.serializers import SiteAddressSerializer
from contact.models import Contact
from work_planning_management.models import Job

def po_number_generated():
    """
    Generate a new purchase order number based on existing numbers.

    Returns:
        str: The newly generated purchase order number.
    """

    # Check if any existing PO numbers exist
    existing_purchases = PurchaseOrder.objects.all()
    existing_purchases = existing_purchases.order_by('-created_at').first()

    new_po_number = 'IFB0001'  # Default starting PO number

    if existing_purchases:
        if existing_purchases.po_number:
            last_po_number = existing_purchases.po_number
            last_po_number_int = int(last_po_number[3:])  # Extract the numeric part
            new_po_number_int = last_po_number_int + 1
            new_po_number = f'IFB{str(new_po_number_int).zfill(4)}'  # Generate the new PO number

    return new_po_number


def update_or_create_inventory(purchase_order, item, quantity):
    # Try to retrieve the existing inventory entry or create a new one
    if not purchase_order.site_address and not purchase_order.inventory_location_id:
        raise ValueError('Inventory cannot be added if both Inventory Location and Site Address is not selected in purchase order, either of them is required.')
    
    inventory = None

    if purchase_order.inventory_location_id and not inventory:

        inventory, created = Inventory.objects.get_or_create(
            item_id=item.item,
            inventory_location = purchase_order.inventory_location_id,
            defaults={
                'total_inventory': quantity
            }
        )
    
    if purchase_order.site_address and not inventory:

        inventory, created = Inventory.objects.get_or_create(
            item_id=item.item,
            site_address = purchase_order.site_address,
            defaults={
                'total_inventory': quantity
            }
        )
    
    if not created:
        # If the inventory entry already exists, update the total_inventory
        inventory.total_inventory = F('total_inventory') + quantity
        inventory.save()

    return inventory

def get_paginated_data(request, queryset, serializer_class, search_field=None):
    search_value = request.GET.get('search[value]', '')
    vendor_query = Q()  # Initialize an empty Q object for vendor filtering
    data_queryset = queryset

    if search_value and search_field:
        data_queryset = data_queryset.filter(**{f'{search_field}__icontains': search_value})

    # Handle filter parameters sent through the AJAX request
    vendor_search = request.GET.get('vendor')
    if vendor_search:
        # Filter vendors based on first_name, last_name, and email
        vendor_query |= Q(vendor_id__first_name__icontains=vendor_search)
        vendor_query |= Q(vendor_id__last_name__icontains=vendor_search)
        vendor_query |= Q(vendor_id__email__icontains=vendor_search)

    location = request.GET.get('location')
    status = request.GET.get('status')
    
    # Apply filters to the queryset based on filter parameters
    if location:
        data_queryset = data_queryset.filter(inventory_location_id__name__icontains=location)
    if status:
        data_queryset = data_queryset.filter(status=status)
   
    if  vendor_query:
        data_queryset = data_queryset.filter(vendor_query)
            
    paginator = Paginator(data_queryset, 25)
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 25))
    page_number = (start // length) + 1
    page_obj = paginator.get_page(page_number)

    serializer = PurchaseOrderListSerializer(page_obj, many=True)

    response_data = {
            "draw": int(request.GET.get('draw', 1)),
            "recordsTotal": data_queryset.count(),
            "recordsFiltered": paginator.count,
            "data": serializer.data,
        }
    return response_data

def get_paginated_data_for_web(request, queryset, search_field=None):
    search_params = request.query_params.get('q', '')
    if search_params:
        search_fields = search_field
        q_objects = Q()

        # Construct a Q object to search across multiple fields dynamically
        for field in search_fields:
            q_objects |= Q(**{f'{field}__icontains': search_params})

        queryset = queryset.filter(q_objects)
    
    vendor_query = Q()  # Initialize an empty Q object for vendor filtering
    data_queryset = queryset

    # Handle filter parameters sent through the AJAX request
    vendor_search = request.GET.get('vendor')
    if vendor_search:
        # Filter vendors based on first_name, last_name, and email
        vendor_query |= Q(vendor_id__first_name__icontains=vendor_search)
        vendor_query |= Q(vendor_id__last_name__icontains=vendor_search)
        vendor_query |= Q(vendor_id__email__icontains=vendor_search)

    location = request.GET.get('location')
    status = request.GET.get('status')
    
    # Apply filters to the queryset based on filter parameters
    if location:
        data_queryset = data_queryset.filter(inventory_location_id__name__icontains=location)
    if status:
        data_queryset = data_queryset.filter(status=status)
   
    if  vendor_query:
        data_queryset = data_queryset.filter(vendor_query)
            
    paginator = Paginator(data_queryset, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    return page_obj
    
    
def get_order_items(data):
    # Access item values using dictionary indexing and looping
    items = []
    for key, value in data.items():
        if key.startswith('items[') and key.endswith('][price]'):
            item_id = key.split('[')[1].split(']')[0]
            price = value
            quantity = data[f'items[{item_id}][quantity]']
            row_total = data[f'items[{item_id}][rowTotal]']
            items.append({'item_id': item_id, 'price': price, 'quantity': quantity, 'row_total': row_total})
    
    return items 



def get_vendor_data(request):
    if request.method == "GET":
        vendor_id = request.GET.get("id")

        try:
            # Retrieve vendor data using the vendor_id
            vendor_data = Vendor.objects.filter(id=vendor_id).first()
            serializer = VendorSerializer(vendor_data)

            item_list = Item.objects.filter(vendor_id=vendor_data)
            item_serializer = ItemSerializer(item_list, many=True)


            response_data = {
                "vendor_data": serializer.data,
                "item_list": item_serializer.data
            }

            return JsonResponse(response_data, status=status.HTTP_200_OK)
            
        except Vendor.DoesNotExist:
            return JsonResponse({"error": "Vendor not found OR You are not authorized to perform this action."}, status=404)

    return JsonResponse({"error": "Invalid request"}, status=400)

def get_inventory_location_data(request):
    if request.method == "GET":
        inventory_location_id = request.GET.get("id")

        try:
            # Retrieve InventoryLocation data using the vendor_id
            inventory_location_data = InventoryLocation.objects.filter(id=inventory_location_id).first()
            serializer = InventoryLocationSerializer(inventory_location_data)
            return create_api_response(status_code=status.HTTP_200_OK,
                                message="Vendor data",
                                 data=serializer.data)
            
        except Vendor.DoesNotExist:
            return JsonResponse({"error": "Vendor not found OR You are not authorized to perform this action."}, status=404)

    return JsonResponse({"error": "Invalid request"}, status=400)


def get_site_address(request):
    if request.method == "GET":
        customer_id = request.GET.get("customer_id")

        try:
            # Retrieve InventoryLocation data using the vendor_id
            site_address_data = SiteAddress.objects.filter(user_id__id=customer_id)
            serializer = SiteAddressSerializer(site_address_data, many=True)
            return create_api_response(status_code=status.HTTP_200_OK,
                                message="Site Address data",
                                 data=serializer.data)
            
        except Vendor.DoesNotExist:
            return JsonResponse({"error": "Site Address not found OR You are not authorized to perform this action."}, status=404)

    return JsonResponse({"error": "Invalid request"}, status=400)


def filter_purchase_order(data_access_value, user):
    # Define a mapping of data access values to corresponding filters.
    filter_mapping = {
        "self": Q(created_by=user),
        "all": Q(),  # An empty Q() object returns all data.
    }
    queryset = PurchaseOrder.objects.all().distinct().order_by('-created_at')
    
    if user.roles.name == "projects_admin_(IT)":
        queryset =  queryset.filter(filter_mapping.get(data_access_value, Q())
        )
    
    else:
        queryset = queryset.filter(filter_mapping.get(data_access_value, Q()))
    return queryset 

class PurchaseOrderListView(CustomAuthenticationMixin,generics.ListAPIView):
    """

    View to get the listing of all Purchase Orders.

    Supports both HTML and JSON response formats.
    """
    renderer_classes = [TemplateHTMLRenderer,JSONRenderer]
    filter_backends = [filters.SearchFilter]
    serializer_class = PurchaseOrderSerializer
    search_fields = ['po_number',]
    template_name = 'purchase_order_list.html'
    ordering_fields = ['created_at'] 
    queryset = PurchaseOrder.objects.all()
    
    def get_queryset(self, data_access_value):
        """
        Get the queryset based on filtering parameters from the request.
        """
        queryset = super().get_queryset()
        
        # Define a mapping of data access values to corresponding filters.
        filter_mapping = {
            "self": Q(created_by=self.request.user),
            "all": Q(),  # An empty Q() object returns all data.
        }
        queryset = queryset.filter(filter_mapping.get(data_access_value, Q()))

        # Order the queryset based on the 'ordering_fields'
        ordering = self.request.GET.get('ordering')
        if ordering in self.ordering_fields:
            queryset = queryset.order_by(ordering)

        return queryset
    
    def get_filter_queryset(self, queryset):
        filters = {
            'status': self.request.GET.get('status'),
            'vendor': self.request.GET.get('vendor'),
            'sub_contractor': self.request.GET.get('sub_contractor'),
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
                    queryset = queryset.filter(
                        Q(po_date__gte=start_date, po_date__lte=end_date) |
                        Q(po_due_date__gte=start_date, po_due_date__lte=end_date)
                    )
                elif filter_name == 'vendor':
                    queryset = queryset.filter(vendor_id__email=filter_value)
                elif filter_name == 'sub_contractor':
                    queryset = queryset.filter(sub_contractor_id__email=filter_value)
                else:
                    # For other filters, apply the corresponding filters on the queryset
                    filter_mapping = {
                        'status': 'status',
                    }
                    queryset = queryset.filter(**{filter_mapping[filter_name]: filter_value.strip()})
        
        return queryset
    
    def get_paginated_queryset(self, base_queryset):
        items_per_page = 20 
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
    
    def get_searched_queryset(self, queryset):
        search_params = self.request.query_params.get('q', '')
        if search_params:
            search_fields = self.search_fields
            q_objects = Q()

            # Construct a Q object to search across multiple fields dynamically
            for field in search_fields:
                q_objects |= Q(**{f'{field}__icontains': search_params})

            queryset = queryset.filter(q_objects)
        
        return queryset

    def get(self, request, *args, **kwargs):
        # Call the handle_unauthenticated method to handle unauthenticated access
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self, "purchase_order", HasListDataPermission, 'list'
        )
        # Check if authenticated_user is a redirect response
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect
        

       # Get the filtered queryset using get_queryset method
        try:
            queryset = self.get_queryset(data_access_value)  # Replace with your queryset retrieval logic
            queryset = self.get_filter_queryset(queryset)
            queryset = self.get_searched_queryset(queryset)
            queryset = self.get_paginated_queryset(queryset)

            if request.accepted_renderer.format == 'html':
                context = {
                    'status_list':STATUS_CHOICES,
                    'orders': queryset,
                    'search_fields': self.search_fields,
                    'search_value': request.query_params.get('q', '') if isinstance(request.query_params.get('q', []), str) else ', '.join(request.query_params.get('q', []))
                }
                return render_html_response(context, self.template_name)
        except Exception as e:
            print(e)
            return JsonResponse({"error": str(e)})


class PurchaseOrderAddView(CustomAuthenticationMixin, generics.CreateAPIView):
    """
    View for adding or updating a Purchase Order.
    Supports both HTML and JSON response formats.
    """
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'purchase_order_form.html'
    serializer_class = PurchaseOrderSerializer


    def get(self, request, *args, **kwargs):
        """
        Handle GET request to display a form for updating a Purchase Order.
        If the Purchase Order exists, retrieve the serialized data and render the HTML template.
        If the Purchase Order does not exist, render the HTML template with an empty serializer.
        """
        # Call the handle_unauthenticated method to handle unauthenticated access
        authenticated_user, data_access_value = check_authentication_and_permissions(
           self,"purchase_order", HasCreateDataPermission, 'add'
        )
        
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect

        vendor_list = Vendor.objects.all()
        inventory_location_list = InventoryLocation.objects.all()
        tax_rate = AdminConfiguration.objects.all().first()
        customer_list = User.objects.filter(roles__name='Customer').all()
        sub_contractor_list = Contact.objects.filter(contact_type__name='Sub-Contractor').all()
        job_list = Job.objects.filter(status__in=['pending', 'in-progress']).all()
        
           
        if request.accepted_renderer.format == 'html':
           
            
            context = {
                'vendor_list':vendor_list, 
                'inventory_location_list':inventory_location_list,
                'customer_list': customer_list,
                'tax_rate':tax_rate,
                'new_po_number':po_number_generated(),
                'sub_contractor_list': sub_contractor_list,
                'job_list': job_list
            }
            return render_html_response(context,self.template_name)
        else:
            return create_api_response(status_code=status.HTTP_201_CREATED,
                                message="GET Method Not Alloweded",)
        

    def post(self, request, *args, **kwargs):
        """
        Handle POST request to add a requirement.
        """
        po_number = po_number_generated()
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            purchase_order = serializer.save(
                created_by=request.user, po_number=po_number
            )
            
            if purchase_order.status == 'pending':
                message = f"Your Purchase Order has been save as draft successfully!"
            else:
                message = f"Your Purchase Order has been {purchase_order.status[1]} successfully!"
                

            messages.success(request, message)
            return JsonResponse({'success': True,  'status':status.HTTP_204_NO_CONTENT})  # Return success response

        return JsonResponse({'success': False, 'errors': serializer.errors, 'status':status.HTTP_400_BAD_REQUEST}) 
        

class PurchaseOrderView(CustomAuthenticationMixin,generics.RetrieveAPIView):
    """

    View to get the listing of all Purchase Orders.

    Supports both HTML and JSON response formats.
    """
    renderer_classes = [TemplateHTMLRenderer,JSONRenderer]
    template_name = 'purchase_order_view.html'
    serializer_class = PurchaseOrderViewSerializer
    queryset = PurchaseOrder.objects.all()

    def get_object(self, data_access_value):
        queryset = super().get_queryset()
        pk = self.kwargs.get('purchase_order_id', None)
        instance = None

        if queryset and data_access_value and pk:
            # Define a mapping of data access values to corresponding filters
            filter_mapping = {
                "self": Q(created_by=self.request.user),
                "all": Q(),  # An empty Q() object returns all data
            }

            queryset = queryset.filter(filter_mapping.get(data_access_value, Q())).all()
            instance = queryset.filter(pk=pk).first()

        return instance
    
    def get(self, request, *args, **kwargs):
        # Get the filtered queryset using get_queryset method
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self, "purchase_order", HasViewDataPermission, 'view'
        )
        # Check if authenticated_user is a redirect response
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect
        
        instance = self.get_object(data_access_value)
        if not instance:
            messages.error(request, "You are not authorized to perform this action.")
            return redirect(reverse('purchase_order_list'))

        serializer = self.get_serializer(instance)

        invoice_item_list = PurchaseOrderInvoice.objects.filter(
            purchase_order_id=instance,
        ).order_by('-created_at').all()
        
        presigned_url = ""
        file_name = ''


        if request.accepted_renderer.format == 'html':
            context = {
                'purchase_order':serializer.data,
                'invoice_item_list':invoice_item_list,
                'presigned_url':presigned_url,
                'file_name':file_name
            }
            return render_html_response(context, self.template_name)
            
            
      
class PurchaseOrderUpdateView(CustomAuthenticationMixin, generics.UpdateAPIView):
    """
    View for adding or updating a Purchase Order.
    Supports both HTML and JSON response formats.
    """
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'purchase_order_form.html'
    serializer_class = PurchaseOrderSerializer
    queryset = PurchaseOrder.objects.filter(status__in=["pending", "sent_for_approval"]).all()

    def get_object(self, data_access_value):
        pk = self.kwargs.get('purchase_order_id', '')
        queryset = super().get_queryset()
        instance = None

        if pk and queryset and data_access_value:
            # Define a mapping of data access values to corresponding filters
            filter_mapping = {
                "self": Q(created_by=self.request.user),
                "all": Q(),  # An empty Q() object returns all data
            }
            
            
            # Get the appropriate filter from the mapping based on the data access value,
            # or use an empty Q() object if the value is not in the mapping
            instance = queryset.filter(
                (Q(pk=pk)) & filter_mapping.get(data_access_value, Q())
            ).first()
        
        return instance
    
    def get(self, request, *args, **kwargs):
        """
        Handle GET request to display a form for updating a Purchase Order.
        If the Purchase Order exists, retrieve the serialized data and render the HTML template.
        If the Purchase Order does not exist, render the HTML template with an empty serializer.
        """
        # Call the handle_unauthenticated method to handle unauthenticated access
        authenticated_user, data_access_value = check_authentication_and_permissions(
           self,"purchase_order", HasUpdateDataPermission, 'change'
        )
        
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect
        
        instance = self.get_object(data_access_value)
        if not instance:
            messages.error(request, "You are not authorized to perform this action.")
            return redirect(reverse('purchase_order_list'))

        vendor_list = Vendor.objects.all()
        customer_list = User.objects.filter(roles__name='Customer').all()
        site_address_list = SiteAddress.objects.filter(user_id__in=customer_list).all()
        inventory_location_list = InventoryLocation.objects.all()
        tax_rate = AdminConfiguration.objects.first()
        sub_contractor_list = Contact.objects.filter(contact_type__name='Sub-Contractor').all()
        job_list = Job.objects.filter(status__in=['pending', 'in-progress']).all()

        item_list = None
        if instance.vendor_id:
            item_list = Item.objects.filter(vendor_id=instance.vendor_id).all()
        
        serializer = self.get_serializer(instance)

        if request.accepted_renderer.format == 'html':
            context = {
                'vendor_list':vendor_list, 
                'sub_contractor_list': sub_contractor_list,
                'job_list': job_list,
                'inventory_location_list':inventory_location_list,
                'customer_list': customer_list,
                'site_address': site_address_list,
                'item_list':item_list,
                'tax_rate':tax_rate,
                'purchase_order':instance,
                'existingPurchaseOrderData':serializer.data,
            }
            return render_html_response(context, self.template_name)
        else:
            return create_api_response(status_code=status.HTTP_201_CREATED,
                                message="GET Method Not Alloweded",)
            
        
    def post(self, request, *args, **kwargs):
        """
        Handle POST request to add a requirement.
        """
        # Call the handle_unauthenticated method to handle unauthenticated access
        authenticated_user, data_access_value = check_authentication_and_permissions(
           self,"purchase_order", HasUpdateDataPermission, 'change'
        )
        
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect
        
        instance = self.get_object(data_access_value)
        if not instance:
            messages.error(request, "You are not authorized to perform this action.")
            return redirect(reverse('purchase_order_list'))

        serializer = self.serializer_class(instance=instance, data=request.data)
        if serializer.is_valid():
            instance = serializer.update(
                instance=instance,
                validated_data=serializer.validated_data
            )
            
            if instance.status == "approved":
                instance.approved_by = request.user
                instance.save()
                
            message = f"Your Purchase Order has been {instance.status} successfully!"
                
            messages.success(request, message)
            return JsonResponse({'success': True,  'status':status.HTTP_204_NO_CONTENT})  # Return success response

        return JsonResponse({'success': False, 'errors': serializer.errors, 'status':status.HTTP_400_BAD_REQUEST}) 

class PurchaseOrderConvertToInvoiceView(CustomAuthenticationMixin,generics.ListAPIView):
    """

    View to get the listing of all Purchase Orders.

    Supports both HTML and JSON response formats.
    """
    renderer_classes = [TemplateHTMLRenderer,JSONRenderer]
    template_name = 'purchase_order_invoice.html'
    serializer_class = PurchaseOrderViewSerializer
    queryset = PurchaseOrder.objects.all()

    def get_object(self, data_access_value):
        queryset = super().get_queryset()
        pk = self.kwargs.get('purchase_order_id', None)
        instance = None

        if queryset and data_access_value and pk:
            # Define a mapping of data access values to corresponding filters
            filter_mapping = {
                "self": Q(created_by=self.request.user),
                "all": Q(),  # An empty Q() object returns all data
            }

            queryset = queryset.filter(filter_mapping.get(data_access_value, Q()) & (Q(status="approved") | Q(status="partially_completed"))).all()
            instance = queryset.filter(pk=pk).first()

        return instance
    
    def get(self, request, *args, **kwargs):
        # Get the filtered queryset using get_queryset method
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self, "purchase_order", HasViewDataPermission, 'view'
        )
        # Check if authenticated_user is a redirect response
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect
        
        instance = self.get_object(data_access_value)
        if not instance:
            messages.error(request, "You are not authorized to perform this action.")
            return redirect(reverse('purchase_order_list'))

        serializer = self.get_serializer(instance)
        
        if request.accepted_renderer.format == 'html':
            context = { 'purchase_order':serializer.data }
            return render_html_response(context, self.template_name)
    
    def post(self, request, *args, **kwargs):
        """
        Handle POST request to create a purchase order invoice and update received inventory.

        Args:
            request: The HTTP request object.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            JsonResponse: JSON response with success status and appropriate message.

        Note:
        This method processes a POST request to create a purchase order invoice and update the received inventory.
        It also checks if the received inventory matches the total quantity of the purchase order items and updates the purchase order status accordingly.
        """
        # Get the filtered queryset using get_queryset method
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self, "purchase_order", HasViewDataPermission, 'view'
        )
        # Check if authenticated_user is a redirect response
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect
        
        instance = self.get_object(data_access_value)
        if not instance:
            messages.error(request, "You are not authorized to perform this action.")
            return redirect(reverse('purchase_order_list'))

        serializer = PurchaseOrderInvoiceSerializer(data=request.data)

        if serializer.is_valid():
            try:
                serializer.save(purchase_order_id=instance)
                messages.success(request, "Invoice aaded successfully")
                return JsonResponse({'success': True,  'status':status.HTTP_204_NO_CONTENT})
            except ValidationError as error:
                return JsonResponse({'success': False, 'errors': error.detail, 'status':status.HTTP_400_BAD_REQUEST})
        
        return JsonResponse({'success': False, 'errors': serializer.errors, 'status':status.HTTP_400_BAD_REQUEST})
        # # Get the purchase order based on the provided purchase_order_id
        # purchase_order = self.get_purchase_order().filter(pk=kwargs.get('purchase_order_id')).first()

        # # Initialize invoice serializer with request data
        # invoice_serializer = PurchaseOrderInvoiceSerializer(data=request.data)

        # # Deserialize the purchase_order_items from JSON
        # purchase_order_items = json.loads(request.POST.get('purchase_order_items'))

        # # Create a list of received inventory serializers for each item
        # received_inventory_serializers = [
        #     PurchaseOrderReceivedInventorySerializer(data=item)
        #     for item in purchase_order_items
        # ]

        # # Combine all serializers, including the invoice serializer
        # all_serializers = [invoice_serializer] + received_inventory_serializers

        # # Check if all serializers are valid
        # all_valid = all(serializer.is_valid() for serializer in all_serializers)

        # if all_valid:
        #     with transaction.atomic():
        #         invoice_serializer.validated_data['purchase_order_id'] = purchase_order
                
        #         from rest_framework import serializers
                
                
        #         error_messages = []

        #         for serializer in received_inventory_serializers:
        #             purchase_order_item_id = serializer.validated_data['purchase_order_item_id']
        #             received_inventory = PurchaseOrderReceivedInventory.objects.filter(
        #                 purchase_order_item_id=purchase_order_item_id,
        #                 purchase_order_item_id__purchase_order_id=purchase_order,
        #                 purchase_order_item_id__purchase_order_id__inventory_location_id=purchase_order.inventory_location_id
        #             ).first()

        #             cumulative_received_quantity = serializer.validated_data.get('received_inventory')
        #             if serializer.validated_data.get('received_inventory') is None:
        #                 # Handle the case where received_inventory is None (e.g., return an error)
        #                 error_message = f"Received inventory is missing for purchase order item {serializer.validated_data['purchase_order_item_id'].id}."
        #                 error_data = {
        #                     'purchase_order_item_id': str(serializer.validated_data['purchase_order_item_id'].id),
        #                     'error_message': error_message
        #                 }
        #                 error_messages.append(error_data)
        #             else:
        #                 if received_inventory:
        #                     cumulative_received_quantity += received_inventory.received_inventory

        #                 if cumulative_received_quantity is not None and cumulative_received_quantity > serializer.validated_data['purchase_order_item_id'].quantity:
        #                     error_message = f"Received quantity exceeds available quantity."
        #                     error_data = {
        #                         'purchase_order_item_id': str(serializer.validated_data['purchase_order_item_id'].id),
        #                         'error_message': error_message
        #                     }
        #                     error_messages.append(error_data)
        #                 else:
        #                     serializer.is_valid()

        #         # Check if any errors were encountered
        #         if error_messages:
        #             return JsonResponse({'success': False, 'errors': error_messages, 'status': status.HTTP_400_BAD_REQUEST})

        #         # No errors, proceed with saving
        #         invoice = invoice_serializer.save()
        #         for serializer in received_inventory_serializers:
        #             purchase_order_item_id = serializer.validated_data['purchase_order_item_id']
        #             received_inventory = PurchaseOrderReceivedInventory.objects.filter(
        #                 purchase_order_item_id=purchase_order_item_id,
        #                 purchase_order_item_id__purchase_order_id=purchase_order,
        #                 purchase_order_item_id__purchase_order_id__inventory_location_id=purchase_order.inventory_location_id
        #             ).first()

        #             cumulative_received_quantity = serializer.validated_data['received_inventory']

        #             if received_inventory:
        #                 cumulative_received_quantity += received_inventory.received_inventory
                    
        #             received_inventory = serializer.save(purchase_order_invoice_id=invoice)
        #             try:
        #                 update_or_create_inventory(purchase_order, serializer.validated_data['purchase_order_item_id'], cumulative_received_quantity)
        #             except ValueError as e:
        #                 messages.error(request, str(e))
        #                 return JsonResponse({'success': False, 'status':status.HTTP_400_BAD_REQUEST})


            
            
        #     # Calculate the total received inventory
        #     total_received_inventory = PurchaseOrderReceivedInventory.objects.filter(
        #         purchase_order_item_id__purchase_order_id = purchase_order.id,
        #         purchase_order_item_id__purchase_order_id__inventory_location_id =   purchase_order.inventory_location_id  
        #     ).aggregate(total_received_inventory=Sum('received_inventory'))['total_received_inventory']
            
        #     # Calculate the total quantity
        #     total_quantity = PurchaseOrderItem.objects.filter(
        #         purchase_order_id=purchase_order.id,
        #         purchase_order_id__inventory_location_id =   purchase_order.inventory_location_id  
        #     ).aggregate(total_quantity=Sum('quantity'))['total_quantity']
            
        #     # Check if the total received inventory is equal to the total quantity
        #     if total_received_inventory is not None and total_quantity is not None and total_received_inventory == total_quantity:
        #         purchase_order.status = 'completed'  # Update the status
        #         purchase_order.save()  # Save the updated status               
        #     else:
        #         purchase_order.status = 'partially_completed' 
            
        #     purchase_order.save()
        #     messages.success(request, "Invoice aaded successfully")
        #     return JsonResponse({'success': True,  'status':status.HTTP_204_NO_CONTENT})
        
        # else:
        #     errors = {}
        #     for serializer in all_serializers:
        #         if not serializer.is_valid():
        #             errors.update(serializer.errors)


class PurchaseOrderInvoiceView(CustomAuthenticationMixin, generics.RetrieveAPIView):
    """
    Retrieve and display a purchase order invoice along with related purchase order items and additional details.

    Attributes:
        renderer_classes (list): List of renderer classes for the view.
        template_name (str): The name of the HTML template used for rendering.
    """

    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'purchase_order_invoice_view.html'
    
    def get(self, request, *args, **kwargs):
        """
        Handle GET request to retrieve and display a purchase order invoice and related details.

        Args:
            request: The HTTP request object.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            JsonResponse: JSON response containing invoice data and related details.
        """

        # Check authentication and permissions for the authenticated user
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self, "purchase_order", HasViewDataPermission, 'view'
        )

        # Get the purchase order invoice based on the provided invoice_id
        purchase_order_invoice = PurchaseOrderInvoice.objects.filter(pk=kwargs.get('invoice_id')).first()

        # Get related purchase order items for the invoice
        purchase_order_items = PurchaseOrderReceivedInventory.objects.filter(
            purchase_order_invoice_id=purchase_order_invoice
        )

        presigned_url = ""
        file_name = ''
        comments = ''

        # Extract comments and presigned URL from the purchase order invoice
        if purchase_order_invoice:
            comments = purchase_order_invoice.comments
            if purchase_order_invoice.invoice_pdf_path:
                presigned_url = generate_presigned_url(purchase_order_invoice.invoice_pdf_path),
                file_name =  purchase_order_invoice.invoice_pdf_path.split('/')[-1]
        
        # Create a list of dictionaries containing required attributes from purchase_order_items
        items_list = []
        for item in purchase_order_items:
            items_list.append({
                'received_inventory': item.received_inventory,
                'quantity': item.purchase_order_item_id.quantity,
                'unit_price': item.purchase_order_item_id.unit_price,
                'item_name': item.purchase_order_item_id.item_name,
            })

        # Prepare the context data for rendering the template
        context = {
            'purchase_order_items': items_list,
            'presigned_url': presigned_url,
            'file_name': file_name,
            'comments': comments
        }

        # Create an API response with the context data
        return create_api_response(status_code=status.HTTP_200_OK, message="Invoice DATA", data=context)
        
        
class PurchaseDeleteView(CustomAuthenticationMixin, generics.DestroyAPIView):
    """
    Delete a purchase order based on the provided purchase_order_id.

    Attributes:
        renderer_classes (list): List of renderer classes for the view.
        template_name (str): The name of the HTML template used for rendering.
    """

    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'purchase_order_view.html'
    
    def delete(self, request, *args, **kwargs):
        """
        Handle DELETE request to delete a purchase order.

        Args:
            request: The HTTP request object.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            Response: JSON response indicating the success or failure of the delete operation.
        """

        # Check authentication and permissions for the authenticated user
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self, "purchase_order", HasDeleteDataPermission, 'delete'
        )

        # Check if authenticated_user is a redirect response
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect

        # Define a mapping of data access values to corresponding filters
        filter_mapping = {
            "self": Q(created_by=self.request.user),
            "all": Q(),  # An empty Q() object returns all data
        }
       
        # Get the purchase order based on the provided purchase_order_id
        base_queryset = PurchaseOrder.objects.filter(pk=kwargs.get('purchase_order_id')).first()

        if base_queryset:
            # Delete the purchase order
            base_queryset.delete()
            return Response(
                {"message": "Your Purchase Order has been deleted successfully."},
                status=status.HTTP_204_NO_CONTENT
            )
        else:
            return Response(
                {"message": "Purchase Order not found or you don't have permission to delete."},
                status=status.HTTP_404_NOT_FOUND
            )
