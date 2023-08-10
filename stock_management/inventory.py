from django.shortcuts import render, redirect
from django.conf import settings
from infinity_fire_solutions.aws_helper import *
from infinity_fire_solutions.permission import *
from .models import *
from .inventory_serializers import *
from infinity_fire_solutions.response_schemas import *
from django.contrib import messages
from rest_framework import generics, status, filters
from rest_framework.renderers import TemplateHTMLRenderer, JSONRenderer
from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError


class InventoryView(CustomAuthenticationMixin, generics.CreateAPIView):
    """
    View for adding  a inventory.
    Supports both HTML and JSON response formats.
    """
    # serializer_class = InventoryAddSerializer
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'inventory.html'
    swagger_schema = None
    
    def get_queryset(self):
        """
        Get the filtered queryset for inventorys based on the authenticated user.
        """
        authenticated_user, data_access_value = check_authentication_and_permissions(
           self,"Requirement", HasCreateDataPermission, 'detail'
        )
        
        # Define a mapping of data access values to corresponding filters.
        filter_mapping = {
            "self": Q(user_id=self.request.user ),
            "all": Q(),  # An empty Q() object returns all data.
        }
        
        queryset = Item.objects.filter(filter_mapping.get(data_access_value, Q()))
        item = queryset.filter(pk= self.kwargs.get('item_id'),  item_type = 'item').first()
        return item
       
    
    def get(self, request, *args, **kwargs):
        # This method handles GET requests for updating an existing Inventory object.
        item_instance = self.get_queryset()
        inventory_location_list = InventoryLocation.objects.all()

        inventory_data = Inventory.objects.filter(
            Q(inventory_location__in=inventory_location_list) & Q(item_id=item_instance)
        )
        if request.accepted_renderer.format == 'html':
            context = {
                'inventory_data': inventory_data,
                'inventory_location_list':inventory_location_list,
                'item_instance':item_instance
                }
            return render_html_response(context, self.template_name)
        else:
            messages.error(request, "You are not authorized to perform this action")
            return redirect(reverse('inventory_list'))

    def post(self, request, *args, **kwargs):
        """
        Handle POST request to add a requirement.
        """
        # Call the handle_unauthenticated method to handle unauthenticated access.
        item_instance = self.get_queryset()
        data = request.POST.copy()  # Create a copy of the QueryDict
        csrf_token = data.pop('csrfmiddlewaretoken', None)  # Remove csrfmiddlewaretoken
        
        for key, value in data.items():
            if key.startswith('total_inventory_'):
                inventory_location_id = key.replace('total_inventory_', '')
                inventory_location = InventoryLocation.objects.get(id=inventory_location_id)
                
                # Create a new Inventory instance
                total_inventory = float(value.strip())
            
                assigned_inventory_key = 'assigned_inventory_' + inventory_location_id
                assigned_inventory = data.get(assigned_inventory_key, 0) # Convert to float with a default value of 0 if not present
                
                inventory = Inventory.objects.filter(item_id=item_instance,inventory_location = inventory_location).first()
                if inventory:
                    inventory.total_inventory = total_inventory

                else:
                    inventory = Inventory.objects.create(
                        item_id=item_instance,
                        inventory_location=inventory_location,
                        total_inventory=total_inventory,
                    )
                if assigned_inventory:
                    inventory.assigned_inventory = float(assigned_inventory.strip())
                inventory.save()

        message = "Congratulations! your inventory has been added successfully."
        if request.accepted_renderer.format == 'html':
            messages.success(request, message)
            return redirect(reverse('inventory_view', kwargs={'item_id': self.kwargs.get('item_id')}))
            