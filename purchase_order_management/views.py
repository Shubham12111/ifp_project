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
from django.core.paginator import Paginator
from django.db import transaction
from datetime import datetime
from django.db.models import Sum
from django.db.models import F
from stock_management.models import Inventory
import json
from rest_framework.response import Response
from common_app.models import *
from customer_management.serializers import SiteAddressSerializer

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
    search_fields = ['po_number', 'vendor_id__email','inventory_location_id__name','status']
    template_name = 'purchase_order_list.html'
    ordering_fields = ['created_at'] 
    
    def get_queryset(self):
        """
        Get the queryset based on filtering parameters from the request.
        """
        # Call the handle_unauthenticated method to handle unauthenticated access
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self, "purchase_order", HasListDataPermission, 'list'
        )
        # Check if authenticated_user is a redirect response
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect

        base_queryset = filter_purchase_order(data_access_value, self.request.user)

        # Order the queryset based on the 'ordering_fields'
        ordering = self.request.GET.get('ordering')
        if ordering in self.ordering_fields:
            base_queryset = base_queryset.order_by(ordering)

        return base_queryset
    
    def get(self, request, *args, **kwargs):
       # Get the filtered queryset using get_queryset method
        try:
            queryset = self.get_queryset()  # Replace with your queryset retrieval logic
            serializer_class = self.serializer_class()  # Replace with your serializer class
            search_field = 'item_name'  # Replace with the field name you want to search on
            if request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
                return JsonResponse(get_paginated_data(request, queryset, serializer_class, search_field))
            
            if request.accepted_renderer.format == 'html':
                context = {
                    'status_list':STATUS_CHOICES,
                    'orders': get_paginated_data_for_web(request, queryset, self.search_fields),
                    'search_fields': ['po number', 'vendor email','inventory location name','status'],
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
        
           
        if request.accepted_renderer.format == 'html':
           
            
            context = {'vendor_list':vendor_list, 
                       'inventory_location_list':inventory_location_list,
                        'customer_list': customer_list,
                       'tax_rate':tax_rate,
                       'new_po_number':po_number_generated()
                       
                       }
            return render_html_response(context,self.template_name)
        else:
            return create_api_response(status_code=status.HTTP_201_CREATED,
                                message="GET Method Not Alloweded",)
        

    def post(self, request, *args, **kwargs):
        """
        Handle POST request to add a requirement.
        """
        data = request.data
        po_number = po_number_generated()
        with transaction.atomic():
            serializer = self.serializer_class(data=request.data)
            if serializer.is_valid():
                serializer.validated_data['created_by'] = request.user  # Assign the current user instance.
                purchase_order = serializer.save()
                purchase_order.po_number = po_number
                
                purchase_order.save()
                # Access item values using dictionary indexing and looping
                items = []
                for key, value in data.items():
                    if key.startswith('items[') and key.endswith('][price]'):
                        item_id = key.split('[')[1].split(']')[0]
                        price = value
                        quantity = data[f'items[{item_id}][quantity]']
                        row_total = data[f'items[{item_id}][rowTotal]']
                        items.append({'item_id': item_id, 'price': price, 'quantity': quantity, 'row_total': row_total})
                # and 'items' is a list containing extracted item data

                for item in items:
                    item_id = item['item_id']
                    price = item['price']
                    quantity = item['quantity']
                    row_total = item['row_total']
                    item = Item.objects.filter(pk=item_id).first()
                    item_name = item.item_name
                    
                    # Create an instance of PurchaseOrderItem and save it
                    item_row = PurchaseOrderItem(item_id=item_id, unit_price=price, 
                                                 quantity=quantity, row_total=row_total, 
                                                 purchase_order_id=purchase_order,item_name=item_name)
                    item_row.save()
                
                if purchase_order.status == 'pending':
                    message = f"Your Purchase Order has been save as draft successfully!"
                else:
                    message = f"Your Purchase Order has been {purchase_order.status[1]} successfully!"
                    

                messages.success(request, message)
                return JsonResponse({'success': True,  'status':status.HTTP_204_NO_CONTENT})  # Return success response
            else:
                return JsonResponse({'success': False, 'errors': serializer.errors,  
                'status':status.HTTP_400_BAD_REQUEST}) 
        

class PurchaseOrderView(CustomAuthenticationMixin,generics.RetrieveAPIView):
    """

    View to get the listing of all Purchase Orders.

    Supports both HTML and JSON response formats.
    """
    renderer_classes = [TemplateHTMLRenderer,JSONRenderer]
    template_name = 'purchase_order_view.html'
    
    def get(self, request, *args, **kwargs):
        # Get the filtered queryset using get_queryset method
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self, "purchase_order", HasViewDataPermission, 'view'
        )
        # Check if authenticated_user is a redirect response
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect

        
        
        # Define a mapping of data access values to corresponding filters
        filter_mapping = {
            "self": Q(created_by=self.request.user),
            "all": Q(),  # An empty Q() object returns all data
        }
        # Get the appropriate filter from the mapping based on the data access value,
        # or use an empty Q() object if the value is not in the mapping
        base_queryset = PurchaseOrder.objects.filter(filter_mapping.get(data_access_value, Q())).distinct().order_by('-created_at')
        purchase_order = base_queryset.filter(pk=kwargs.get('purchase_order_id')).first()
        
        if purchase_order:
            purchase_order_items = PurchaseOrderItem.objects.filter(purchase_order_id=purchase_order)
            
            invoice_item_list = PurchaseOrderInvoice.objects.filter(purchase_order_id=purchase_order,
                                                                    purchase_order_id__inventory_location_id=purchase_order.inventory_location_id).order_by('-created_at')
            
            presigned_url = ""
            file_name = ''
            if purchase_order.document:
                presigned_url = generate_presigned_url(purchase_order.document),
                file_name =  purchase_order.document.split('/')[-1]


            if request.accepted_renderer.format == 'html':
                context = {'purchase_order':purchase_order,
                        'purchase_order_items':purchase_order_items,
                        'invoice_item_list':invoice_item_list,
                        'presigned_url':presigned_url,
                            'file_name':file_name}
                return render_html_response(context, self.template_name)
        else:
            messages.error(request, "You are not authorized to perform this action.")
            return redirect(reverse('purchase_order_list'))
            
      
class PurchaseOrderUpdateView(CustomAuthenticationMixin, generics.UpdateAPIView):
    """
    View for adding or updating a Purchase Order.
    Supports both HTML and JSON response formats.
    """
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'purchase_order_form.html'
    serializer_class = PurchaseOrderSerializer

    def get_purchase_order(self, *args, **kwargs):
        
        # Call the handle_unauthenticated method to handle unauthenticated access
        authenticated_user, data_access_value = check_authentication_and_permissions(
           self,"purchase_order", HasUpdateDataPermission, 'change'
        )
        
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect

        # Define a mapping of data access values to corresponding filters
        filter_mapping = {
            "self": Q(created_by=self.request.user),
            "all": Q(),  # An empty Q() object returns all data
        }
        # Get the appropriate filter from the mapping based on the data access value,
        # or use an empty Q() object if the value is not in the mapping
        base_queryset = PurchaseOrder.objects.filter(
            (Q(status="pending") | Q(status="sent_for_approval")) & filter_mapping.get(data_access_value, Q())
        ).distinct().order_by('-created_at')        
        return base_queryset
    
    def get(self, request, *args, **kwargs):
        """
        Handle GET request to display a form for updating a Purchase Order.
        If the Purchase Order exists, retrieve the serialized data and render the HTML template.
        If the Purchase Order does not exist, render the HTML template with an empty serializer.
        """
        purchase_order = self.get_purchase_order().filter(pk = kwargs.get('purchase_order_id'))
        purchase_order_data = purchase_order.first()
       

        if request.accepted_renderer.format == 'html':
            # Extract the first purchase order object from the queryset
            if purchase_order_data:
                vendor_list = Vendor.objects.all()
                customer_list = User.objects.filter(roles__name='Customer').all()
                site_address = SiteAddress.objects.filter(user_id__in=customer_list).all()
                inventory_location_list = InventoryLocation.objects.all()
                item_list = Item.objects.filter(vendor_id=purchase_order_data.vendor_id)
                tax_rate = AdminConfiguration.objects.all().first()

                existingPurchaseOrderData = {} 
                
                purchase_order_items_data = PurchaseOrderItem.objects.filter(purchase_order_id=purchase_order_data)  # Assuming a related name of "items" for the items on the PurchaseOrder model
                # Prepare items data
                items_data = [
                    {
                        'item_id': item.id,
                        'price': item.unit_price,
                        'quantity': item.quantity,
                        'row_total': item.row_total,
                       
                    }
                    for item in purchase_order_items_data
                ]
                
                existingPurchaseOrderData = {
                    'vendor_id': purchase_order_data.vendor_id.id,
                    'inventory_location_id': purchase_order_data.inventory_location_id.id if purchase_order_data.inventory_location_id else '',
                    'user_id': purchase_order_data.user_id.id if purchase_order_data.user_id else '',
                    'site_address': purchase_order_data.site_address.id if purchase_order_data.site_address else '',
                    'po_number': purchase_order_data.po_number,
                    'created_at': purchase_order_data.created_at.strftime('%Y-%m-%d'),  # Convert date to string
                    'tax': purchase_order_data.tax,
                    'sub_total': purchase_order_data.sub_total,
                    'discount': purchase_order_data.discount,
                    'notes': purchase_order_data.notes,
                    'grand_total': purchase_order_data.total_amount,
                    'items': items_data,
                    
                    # ... other fields
                }
                presigned_url = ""
                file_name = ""
                if purchase_order_data.document:
                    presigned_url = generate_presigned_url(purchase_order_data.document),
                    file_name =  purchase_order_data.document.split('/')[-1]

                context = {'vendor_list':vendor_list, 
                            'inventory_location_list':inventory_location_list,
                            'customer_list': customer_list,
                            'site_address': site_address,
                            'item_list':item_list,
                            'purchase_order':purchase_order_data,
                            'existingPurchaseOrderData':existingPurchaseOrderData,
                            'presigned_url':presigned_url,
                            'file_name':file_name,
                            'tax_rate':tax_rate}
                return render_html_response(context,self.template_name)
            else:
                messages.error(request, "You are not authorized to perform this action.")
                return redirect(reverse('purchase_order_list'))
        else:
            return create_api_response(status_code=status.HTTP_201_CREATED,
                                message="GET Method Not Alloweded",)
            
        
    def post(self, request, *args, **kwargs):
        purchase_order = self.get_purchase_order().filter(pk = kwargs.get('purchase_order_id'))
        purchase_order_data = purchase_order.first()
        serializer = self.serializer_class(instance = purchase_order_data, data=request.data)
        if serializer.is_valid():
            # You can add any additional processing or validation here
            with transaction.atomic():
                purchase_order = serializer.update(purchase_order_data, validated_data=serializer.validated_data)
                # Process item data
                items_data = get_order_items(request.data)
                existing_item_ids = [item['item_id'] for item in items_data]
                
                # Delete PurchaseOrderItem instances that are not present in existing_item_ids
                PurchaseOrderItem.objects.filter(purchase_order_id=purchase_order).exclude(item_id__in=existing_item_ids).delete()

                for item_data in items_data:
                    item_id = item_data.get('item_id')
                    item = Item.objects.filter(pk=item_id).first()
                    item_name = item.item_name
                    price = item_data.get('price')
                    quantity = item_data.get('quantity')
                    row_total = item_data.get('row_total')
                    
                    # Update or create the PurchaseOrderItem
                    purchase_order_item, created = PurchaseOrderItem.objects.update_or_create(
                        purchase_order_id=purchase_order,
                        item_id=item_id,
                        defaults={
                            'unit_price': price,
                            'quantity': quantity,
                            'row_total': row_total,
                            'item_name':item_name
                        }
                    )
                
                if purchase_order.status == "approved":
                    purchase_order.approved_by = request.user
                    purchase_order.save()
                    
            message = f"Your Purchase Order has been {purchase_order.status} successfully!"

            messages.success(request, message)
            return JsonResponse({'success': True,  'status':status.HTTP_204_NO_CONTENT})  # Return success response
        else:
            return JsonResponse({'success': False, 'errors': serializer.errors,  
            'status':status.HTTP_400_BAD_REQUEST}) 


class PurchaseOrderConvertToInvoiceView(CustomAuthenticationMixin,generics.ListAPIView):
    """

    View to get the listing of all Purchase Orders.

    Supports both HTML and JSON response formats.
    """
    renderer_classes = [TemplateHTMLRenderer,JSONRenderer]
    template_name = 'purchase_order_invoice.html'
    ordering_fields = ['created_at'] 
    
    def get_purchase_order(self, *args, **kwargs):
        
        # Call the handle_unauthenticated method to handle unauthenticated access
        authenticated_user, data_access_value = check_authentication_and_permissions(
           self,"purchase_order", HasCreateDataPermission, 'add'
        )
        
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect

        # Define a mapping of data access values to corresponding filters
        filter_mapping = {
            "self": Q(created_by=self.request.user),
            "all": Q(),  # An empty Q() object returns all data
        }
        # Get the appropriate filter from the mapping based on the data access value,
        # or use an empty Q() object if the value is not in the mapping
        base_queryset = PurchaseOrder.objects.filter(
            (Q(status="approved") | Q(status="partially_completed")) & filter_mapping.get(data_access_value, Q())
        )
        return base_queryset
    
    def get(self, request, *args, **kwargs):
        purchase_order = self.get_purchase_order().filter(pk=kwargs.get('purchase_order_id')).first() 
        purchase_order_items = PurchaseOrderItem.objects.filter(purchase_order_id=purchase_order)
        
        if request.accepted_renderer.format == 'html':
            context = {'purchase_order':purchase_order,
                      'purchase_order_items':purchase_order_items }
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

        # Get the purchase order based on the provided purchase_order_id
        purchase_order = self.get_purchase_order().filter(pk=kwargs.get('purchase_order_id')).first()

        # Initialize invoice serializer with request data
        invoice_serializer = PurchaseOrderInvoiceSerializer(data=request.data)

        # Deserialize the purchase_order_items from JSON
        purchase_order_items = json.loads(request.POST.get('purchase_order_items'))

        # Create a list of received inventory serializers for each item
        received_inventory_serializers = [
            PurchaseOrderReceivedInventorySerializer(data=item)
            for item in purchase_order_items
        ]

        # Combine all serializers, including the invoice serializer
        all_serializers = [invoice_serializer] + received_inventory_serializers

        # Check if all serializers are valid
        all_valid = all(serializer.is_valid() for serializer in all_serializers)

        if all_valid:
            with transaction.atomic():
                invoice_serializer.validated_data['purchase_order_id'] = purchase_order
                
                from rest_framework import serializers
                
                
                error_messages = []

                for serializer in received_inventory_serializers:
                    purchase_order_item_id = serializer.validated_data['purchase_order_item_id']
                    received_inventory = PurchaseOrderReceivedInventory.objects.filter(
                        purchase_order_item_id=purchase_order_item_id,
                        purchase_order_item_id__purchase_order_id=purchase_order,
                        purchase_order_item_id__purchase_order_id__inventory_location_id=purchase_order.inventory_location_id
                    ).first()

                    cumulative_received_quantity = serializer.validated_data.get('received_inventory')
                    if serializer.validated_data.get('received_inventory') is None:
                        # Handle the case where received_inventory is None (e.g., return an error)
                        error_message = f"Received inventory is missing for purchase order item {serializer.validated_data['purchase_order_item_id'].id}."
                        error_data = {
                            'purchase_order_item_id': str(serializer.validated_data['purchase_order_item_id'].id),
                            'error_message': error_message
                        }
                        error_messages.append(error_data)
                    else:
                        if received_inventory:
                            cumulative_received_quantity += received_inventory.received_inventory

                        if cumulative_received_quantity is not None and cumulative_received_quantity > serializer.validated_data['purchase_order_item_id'].quantity:
                            error_message = f"Received quantity exceeds available quantity."
                            error_data = {
                                'purchase_order_item_id': str(serializer.validated_data['purchase_order_item_id'].id),
                                'error_message': error_message
                            }
                            error_messages.append(error_data)
                        else:
                            serializer.is_valid()

                # Check if any errors were encountered
                if error_messages:
                    return JsonResponse({'success': False, 'errors': error_messages, 'status': status.HTTP_400_BAD_REQUEST})

                # No errors, proceed with saving
                invoice = invoice_serializer.save()
                for serializer in received_inventory_serializers:
                    purchase_order_item_id = serializer.validated_data['purchase_order_item_id']
                    received_inventory = PurchaseOrderReceivedInventory.objects.filter(
                        purchase_order_item_id=purchase_order_item_id,
                        purchase_order_item_id__purchase_order_id=purchase_order,
                        purchase_order_item_id__purchase_order_id__inventory_location_id=purchase_order.inventory_location_id
                    ).first()

                    cumulative_received_quantity = serializer.validated_data['received_inventory']

                    if received_inventory:
                        cumulative_received_quantity += received_inventory.received_inventory
                    
                    received_inventory = serializer.save(purchase_order_invoice_id=invoice)
                    try:
                        update_or_create_inventory(purchase_order, serializer.validated_data['purchase_order_item_id'], cumulative_received_quantity)
                    except ValueError as e:
                        messages.error(request, str(e))
                        return JsonResponse({'success': False, 'status':status.HTTP_400_BAD_REQUEST})


            
            
            # Calculate the total received inventory
            total_received_inventory = PurchaseOrderReceivedInventory.objects.filter(
                purchase_order_item_id__purchase_order_id = purchase_order.id,
                purchase_order_item_id__purchase_order_id__inventory_location_id =   purchase_order.inventory_location_id  
            ).aggregate(total_received_inventory=Sum('received_inventory'))['total_received_inventory']
            
            # Calculate the total quantity
            total_quantity = PurchaseOrderItem.objects.filter(
                purchase_order_id=purchase_order.id,
                purchase_order_id__inventory_location_id =   purchase_order.inventory_location_id  
            ).aggregate(total_quantity=Sum('quantity'))['total_quantity']
            
            # Check if the total received inventory is equal to the total quantity
            if total_received_inventory is not None and total_quantity is not None and total_received_inventory == total_quantity:
                purchase_order.status = 'completed'  # Update the status
                purchase_order.save()  # Save the updated status               
            else:
                purchase_order.status = 'partially_completed' 
            
            purchase_order.save()
            messages.success(request, "Invoice aaded successfully")
            return JsonResponse({'success': True,  'status':status.HTTP_204_NO_CONTENT})
        
        else:
            errors = {}
            for serializer in all_serializers:
                if not serializer.is_valid():
                    errors.update(serializer.errors)
            
            return JsonResponse({'success': False, 'errors': errors,  
            'status':status.HTTP_400_BAD_REQUEST})


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
