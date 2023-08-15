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
from .serializers import InventoryLocationSerializer, PurchaseOrderSerializer
from .models import PurchaseOrder
from django.http import JsonResponse
from django.core import serializers
from django.views import View
from django.core.paginator import Paginator

class PurchaseOrderListView(CustomAuthenticationMixin,generics.ListAPIView):
    """

    View to get the listing of all Purchase Orders.

    Supports both HTML and JSON response formats.
    """
    renderer_classes = [TemplateHTMLRenderer,JSONRenderer]
    filter_backends = [filters.SearchFilter]
    search_fields = ['first_name', 'last_name','email']
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
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self, "stock_management", HasListDataPermission, 'list'
        )
        # Check if authenticated_user is a redirect response
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect


        search_value = request.GET.get('search[value]', '')
        
        # Fetch the data from the database
        purchase_orders =  self.get_queryset()
        
        # Filter data based on search value
        if search_value:
            purchase_orders = purchase_orders.filter(item_name__icontains=search_value)
        
        # Set up pagination
        paginator = Paginator(purchase_orders, 25)
        page_number = request.GET.get('start', 0) // 25 + 1
        page_obj = paginator.get_page(page_number)
        
        # Convert the data to JSON format
        data = serializers.serialize("json", page_obj)
        
        if request.accepted_renderer.format == 'html':
            context = {'purchase_orders':purchase_orders}
            return render_html_response(context, self.template_name)
        else:
            print(purchase_orders, "purchase_orders")
        
            return JsonResponse({
                "draw": int(request.GET.get('draw', 1)),
                "recordsTotal": purchase_orders.count(),
                "recordsFiltered": paginator.count,
                "data": data,
            })
            
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
                       'item_list':item_list}
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
        
        message = "Congratulations! your requirement has been added successfully."
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.validated_data['created_by'] = request.user  # Assign the current user instance.
            serializer.save()

            # Process item rows
            item_ids = request.POST.getlist('items[]')
            item_prices = request.POST.getlist('items[][price]')
            item_quantities = request.POST.getlist('items[][quantity]')
            item_total = request.POST.getlist('items[][rowTotal]')
            for item_id, price, quantity in zip(item_ids, item_prices, item_quantities, item_total):
                # Save item row data to your database model
                # Replace this with your actual model and fields
                item_row = PurchaseOrderItem(item_id=item_id, price=price, quantity=quantity, row_total=item_total)
                item_row.save()

            message = "Your Purchase Order has been added successfully!"

            messages.success(request, message)
            return JsonResponse({'success': True,  'status':status.HTTP_204_NO_CONTENT})  # Return success response
        else:
            print(serializer.errors)
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
        purchase_order = base_queryset.filter(pk=kwargs.get('purchase_order_id')) 
        
        if request.accepted_renderer.format == 'html':
            context = {'purchase_order':purchase_order}
            return render_html_response(context, self.template_name)
        