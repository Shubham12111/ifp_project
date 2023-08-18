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
from .serializers import InventoryLocationSerializer, PurchaseOrderSerializer, PurchaseOrderListSerializer
from .models import PurchaseOrder, PurchaseOrderItem
from django.http import JsonResponse
from django.core import serializers
from django.views import View
from django.core.paginator import Paginator
from django.db import transaction
from datetime import datetime

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
    due_date = request.GET.get('due_date')
    order_date = request.GET.get('order_date')

    # Apply filters to the queryset based on filter parameters
    if location:
        data_queryset = data_queryset.filter(location__icontains=location)
    if status:
        data_queryset = data_queryset.filter(status=status)
    if due_date:
        due_date = datetime.strptime(due_date, "%d/%m/%Y").strftime("%Y-%m-%d")
        data_queryset = data_queryset.filter(due_date=due_date)  
    if order_date:
        order_date = datetime.strptime(order_date, "%d/%m/%Y").strftime("%Y-%m-%d")

        data_queryset = data_queryset.filter(order_date=order_date) 

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
            self, "stock_management", HasListDataPermission, 'list'
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
                context = {}
                return render_html_response(context, self.template_name)
        except Exception as e:
            print(e)
            return JsonResponse({"error": str(e)})

            
def get_vendor_data(request):
    if request.method == "GET":
        vendor_id = request.GET.get("id")

        try:
            # Retrieve vendor data using the vendor_id
            vendor_data = Vendor.objects.filter(id=vendor_id).first()
            serializer = VendorSerializer(vendor_data)
            return create_api_response(status_code=status.HTTP_200_OK,
                                message="Vendor data",
                                 data=serializer.data)
            
        except Vendor.DoesNotExist:
            return JsonResponse({"error": "Vendor not found"}, status=404)

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
            return JsonResponse({"error": "Vendor not found"}, status=404)

    return JsonResponse({"error": "Invalid request"}, status=400)

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
           self,"stock_management", HasCreateDataPermission, 'add'
        )
        
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect

        vendor_list = Vendor.objects.all()
        inventory_location_list = InventoryLocation.objects.all()
        item_list = Item.objects.filter(item_type='item')
        if request.accepted_renderer.format == 'html':
           
            
            context = {'vendor_list':vendor_list, 
                       'inventory_location_list':inventory_location_list,
                       'item_list':item_list
                       }
            return render_html_response(context,self.template_name)
        else:
            return create_api_response(status_code=status.HTTP_201_CREATED,
                                message="GET Method Not Alloweded",)
        

    def post(self, request, *args, **kwargs):
        """
        Handle POST request to add a requirement.
        """
        # Call the handle_unauthenticated method to handle unauthenticated access.
        authenticated_user, data_access_value = check_authentication_and_permissions(
           self,"fire_risk_assessment", HasCreateDataPermission, 'add'
        )
        
        data = request.data
        with transaction.atomic():
            serializer = self.serializer_class(data=request.data)
            if serializer.is_valid():
                serializer.validated_data['created_by'] = request.user  # Assign the current user instance.
                purchase_order = serializer.save()

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
                
                message = "Your Purchase Order has been added successfully!"

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
            self, "stock_management", HasListDataPermission, 'list'
        )
        # Check if authenticated_user is a redirect response
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect

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
        
        purchase_order_items = PurchaseOrderItem.objects.filter(purchase_order_id=purchase_order)
        
        if request.accepted_renderer.format == 'html':
            context = {'purchase_order':purchase_order,
                      'purchase_order_items':purchase_order_items }
            return render_html_response(context, self.template_name)
        
        
        
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
           self,"stock_management", HasCreateDataPermission, 'add'
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
        vendor_list = Vendor.objects.all()
        inventory_location_list = InventoryLocation.objects.all()
        item_list = Item.objects.filter(item_type='item')
        
        if request.accepted_renderer.format == 'html':
            # Extract the first purchase order object from the queryset
            if purchase_order_data:
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
                    'inventory_location_id': purchase_order_data.inventory_location_id.id,
                    'po_number': purchase_order_data.po_number,
                    'order_date': purchase_order_data.order_date.strftime('%Y-%m-%d'),  # Convert date to string
                    'due_date': purchase_order_data.due_date.strftime('%Y-%m-%d'),  # Convert date to string
                    'tax': purchase_order_data.tax,
                    'sub_total': purchase_order_data.sub_total,
                    'discount': purchase_order_data.discount,
                    'notes': purchase_order_data.notes,
                    'grand_total': purchase_order_data.total_amount,
                    'items': items_data,
                    # ... other fields
                }
                
                context = {'vendor_list':vendor_list, 
                        'inventory_location_list':inventory_location_list,
                        'item_list':item_list,
                        'purchase_order':purchase_order_data,
                        'existingPurchaseOrderData':existingPurchaseOrderData}
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
                purchase_order = serializer.save()
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

            message = "Your Purchase Order has been updated successfully!"

            messages.success(request, message)
            return JsonResponse({'success': True,  'status':status.HTTP_204_NO_CONTENT})  # Return success response
        else:
            return JsonResponse({'success': False, 'errors': serializer.errors,  
            'status':status.HTTP_400_BAD_REQUEST}) 