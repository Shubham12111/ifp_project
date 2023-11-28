from django.contrib import messages
from django.urls import reverse
from django.shortcuts import render, redirect
from django.http import Http404, JsonResponse, HttpResponse, HttpResponseRedirect
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.decorators.csrf import csrf_exempt

from drf_yasg.utils import swagger_auto_schema

from rest_framework import generics, status, filters
from rest_framework.response import Response
from infinity_fire_solutions.aws_helper import *
from infinity_fire_solutions.permission import *
from rest_framework.renderers import TemplateHTMLRenderer, JSONRenderer

from infinity_fire_solutions.response_schemas import create_api_response, convert_serializer_errors, render_html_response
from infinity_fire_solutions.utils import docs_schema_response_new
from django.views.decorators.csrf import csrf_protect

from .models import *
from .rlo_serializers  import RLOAddSerializer,RLOLetterTemplateSerializer
import os
import pdfkit
from django.template.loader import render_to_string


class RLOListView(CustomAuthenticationMixin,generics.ListAPIView):
    """
    View to get the listing of all RLO.
    Supports both HTML and JSON response formats.
    """
    serializer_class = RLOAddSerializer
    renderer_classes = [TemplateHTMLRenderer,JSONRenderer]
    filter_backends = [filters.SearchFilter]
    # search_fields = ['action', 'description','RBNO','UPRN']
    template_name = 'RLO/rlo_list.html'
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
        # base_queryset = RLO.objects.filter(filter_mapping.get(data_access_value, Q())).distinct().order_by('-created_at')

        base_queryset = RLO.objects.filter(filter_mapping.get(data_access_value, Q())).distinct()

        # Order the queryset based on the 'ordering_fields'
        ordering = self.request.GET.get('ordering')
        if ordering in self.ordering_fields:
            base_queryset = base_queryset.order_by(ordering)

        return base_queryset.order_by('-created_at')

    common_get_response = {
        status.HTTP_200_OK: 
            docs_schema_response_new(
                status_code=status.HTTP_200_OK,
                serializer_class=serializer_class,
                message = "Data retrieved",
                )
    }
    @swagger_auto_schema(operation_id='RLO listing', responses={**common_get_response}) 
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
            context = {'RLO_data': queryset}
            return render_html_response(context, self.template_name)
        else:
            serializer = self.serializer_class(queryset, many=True)
            return create_api_response(
                status_code=status.HTTP_200_OK,
                message="Data retrieved",
                data=serializer.data
            )


class RLOAddView(CustomAuthenticationMixin, generics.CreateAPIView):
    """
    View for adding  a RLO ADD.
    Supports both HTML and JSON response formats.
    """
    serializer_class = RLOAddSerializer
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'RLO/rlo_form.html'


    @swagger_auto_schema(auto_schema=None) 
    def get(self, request, *args, **kwargs):
        """
        Handle GET request to display a form for adding a RLO.
        If the RLO exists, retrieve the serialized data and render the HTML template.
        If the RLO does not exist, render the HTML template with an empty serializer.
        """
      
       
        # Call the handle_unauthenticated method to handle unauthenticated access
        authenticated_user, data_access_value = check_authentication_and_permissions(
        self,"survey", HasCreateDataPermission, 'add'
        )

        if isinstance(authenticated_user, HttpResponseRedirect):
                return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect

        # Filter the queryset based on the user ID
        serializer = self.serializer_class(context={'request': request})
        templates = RLOLetterTemplate.objects.all()
        print(templates)

        # Check if a template has been selected
        selected_template_id = request.GET.get('template_id')
        print(selected_template_id)
        selected_template = None

        if selected_template_id:
            try:
                selected_template = RLOLetterTemplate.objects.get(id=selected_template_id)
            except RLOLetterTemplate.DoesNotExist:
                pass
            
        if request.accepted_renderer.format == 'html':
            context = {'serializer':serializer,'templates':templates,
                                   'selected_template': selected_template,

                          }
                
            return render_html_response(context,self.template_name)
        else:
            return create_api_response(status_code=status.HTTP_201_CREATED,
                                    message="GET Method Not Alloweded",)
       

  
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        print(request.data)
        # Get the selected template ID from the request data
        template_id = request.data.get('template_id')
        print(template_id,"template_id")

        if not template_id:
            # If 'template_id' is not provided, return an error response
            if request.accepted_renderer.format == 'html':
                messages.error(request, "Please select a template.")
                return redirect(reverse('rlo_add'))
            else:
                return create_api_response(status_code=status.HTTP_400_BAD_REQUEST, message="Please select a template.")
                
        message = "Your RLO has been added successfully."
        # breakpoint()
        if serializer.is_valid():
            serializer.validated_data['user_id'] = request.user  # Assign the current user instance
            rlo = serializer.save()

            
            
            # Check if the template_id is valid
            try:
                template = RLOLetterTemplate.objects.get(id=template_id)
                print(template,"template")
            except RLOLetterTemplate.DoesNotExist:
                template = None

            # Update the RLO instance with the selected template (if valid)
            if template:

                rlo.base_template = template
            
            # Save the edited template content to the RLO instance
            edited_content = request.data.get('edited_content')
            if edited_content is not None:
                rlo.edited_content = edited_content
            else:
                rlo.edited_content = template.complete_template
            rlo.save()

            if request.accepted_renderer.format == 'html':
                messages.success(request, message)
                return redirect(reverse('rlo_list'))
            else:
                # Return JSON response with success message and serialized data.
                return create_api_response(status_code=status.HTTP_201_CREATED, message=message, data=serializer.data)

        else:   
            # Return JSON response with error message.
            return create_api_response(status_code=status.HTTP_400_BAD_REQUEST,
                                    message="We apologize for the inconvenience, but please review the below information.",
                                    data=convert_serializer_errors(serializer.errors))




@csrf_protect
def get_template_content(request):
    if request.method == 'GET':
        template_id = request.GET.get('template_id')
        print(template_id)

        try:
            template = RLOLetterTemplate.objects.get(pk=template_id)
            template_content = template.complete_template
            # Use BeautifulSoup to remove HTML tags
            # soup = BeautifulSoup(template_content, 'html.parser')
            # plain_text = soup.get_text()

            return JsonResponse({'template_content': template_content})
        except RLOLetterTemplate.DoesNotExist:
            return JsonResponse({'error': 'Template not found'}, status=404)
        

class RLODeleteView(CustomAuthenticationMixin, generics.DestroyAPIView):
    """
    View for deleting a RLO.
    Supports both HTML and JSON response formats.
    """
    serializer_class = RLOAddSerializer
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    
    common_delete_response = {
        status.HTTP_200_OK: 
            docs_schema_response_new(
                status_code=status.HTTP_200_OK,
                serializer_class=serializer_class,
                message = "RLO has been deleted successfully!",
                ),
        status.HTTP_404_NOT_FOUND: 
            docs_schema_response_new(
                status_code=status.HTTP_404_NOT_FOUND,
                serializer_class=serializer_class,
                message = "RLO not found OR You are not authorized to perform this action.",
                ),

    }
    @swagger_auto_schema(operation_id='STW Requirement Delete', responses={**common_delete_response})
    
    def delete(self, request, *args, **kwargs):
        """
        Handle DELETE request to delete a RLO.
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
        queryset = RLO.objects.filter(filter_mapping.get(data_access_value, Q()), pk=self.kwargs.get('pk'))
        
        rlo_instance = queryset.first()
        print(rlo_instance)

        if rlo_instance:
            # Proceed with the deletion
            rlo_instance.delete()
            messages.success(request, "Your RLO has been deleted successfully!")
            return create_api_response(status_code=status.HTTP_404_NOT_FOUND,
                                        message="Your STW requirement has been deleted successfully!", )
        else:
            messages.error(request, "RLO not found OR You are not authorized to perform this action.")
            return create_api_response(status_code=status.HTTP_404_NOT_FOUND,
                                        message="STW Requirement not found OR You are not authorized to perform this action.", )


class RLOpdfView(CustomAuthenticationMixin, generics.RetrieveAPIView):
    """ vIew to download the template.
    
    """
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'RLO/rlo_pdf.html'
    serializer_class = RLOAddSerializer
    pdf_options = {
        'page-size': 'A4',  # You can change this to 'A4' or custom size
        'margin-top': '10mm',
        'margin-right': '0mm',
        'margin-bottom': '0mm',
        'margin-left': '0mm',
    }
    def save_pdf_from_html(self, context, file_name):
        """
        Save the PDF file from the HTML content.
        Args:
            context (dict): Context data for rendering the HTML template.
            file_name (str): Name of the PDF file.
        Returns:
            Output file path or None.
        """
        output_file = None
        local_folder = '/tmp'

        if local_folder:
            try:
                os.makedirs(local_folder, exist_ok=True)
                output_file = os.path.join(local_folder, file_name)

                # get the html text from the tmplate
                html_content = render_to_string('RLO/rlo_pdf.html', context)

                # create the PDF file for the invoice
                pdfkit.from_string(html_content, output_file, options=self.pdf_options)
                
            except Exception as e:
                # Handle any exceptions that occur during PDF generation
                print("error")

        return output_file


    def get_queryset(self):
        """
        Get the queryset for listing Rlo.

        Returns:
            QuerySet: A queryset of Requirements items filtered based on the authenticated user's ID.
        """
        # Get the model class using the provided module_name string
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self, "fire_risk_assessment", HasViewDataPermission, 'view'
        )
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect

        pk = self.kwargs.get('pk')
         
        return RLO.objects.filter(pk=pk)
    

    @swagger_auto_schema(auto_schema=None)
    def get(self, request, *args, **kwargs):
        """
        Handle GET requests for RLO.

        Args:
            request (HttpRequest): The HTTP request object.

        Returns:
            HttpResponse: The response, either HTML or JSON.
        """
       
        data_instance = self.get_queryset()
        print(data_instance)
    
        if request.accepted_renderer.format == 'html':
             # Pass the edited_content to the PDF template
            if data_instance:
            # Get the first instance from the queryset, assuming there's only one
                data_instance = data_instance[0]
                template_content = data_instance.edited_content
                serializer = self.serializer_class(instance=data_instance, context={'request': request})        
                context = {
                        'serializer': serializer, 
                        'instance': data_instance, 
                        'template_content': template_content,
            }
                return render_html_response(context, self.template_name)
            else:
                messages.error(request, "You are not authorized to perform this action")
                return redirect(reverse('rlo_list'))
    
class RejectRLOView(CustomAuthenticationMixin, generics.CreateAPIView):
    """
    View for rejecting an RLO.
    Supports both HTML and JSON response formats.
    """
    serializer_class = RLOAddSerializer  # Replace with the appropriate serializer
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]

    @swagger_auto_schema(auto_schema=None)
    def post(self, request, rlo_id):
        """
        Handle POST request to reject an RLO.
        Update the RLO's status to 'Rejected' and return a response.
        """
        rlo = get_object_or_404(RLO, pk=rlo_id)
        rlo.status = 'Rejected'  # Update the status as needed
        rlo.save()

        message = "RLO rejected successfully."

        if request.accepted_renderer.format == 'html':
            messages.success(request, message)
            return redirect(reverse('rlo_list'))
        else:
            return create_api_response(
                status_code=status.HTTP_201_CREATED,
                message=message,
            )

class ApproveRLOView(CustomAuthenticationMixin, generics.CreateAPIView):
    """
    View for approving an RLO.
    Supports both HTML and JSON response formats.
    """
    serializer_class = RLOAddSerializer  # Replace with the appropriate serializer
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]


    @swagger_auto_schema(auto_schema=None)
    def post(self, request, rlo_id):
        """
        Handle POST request to approve an RLO.
        Update the RLO's status to 'Approved' and return a response.
        """
        rlo = get_object_or_404(RLO, pk=rlo_id)
        rlo.status = 'Approved'  # Update the status as needed
        rlo.save()

        message = "RLO approved successfully."

        if request.accepted_renderer.format == 'html':
            messages.success(request, message)
            return redirect(reverse('rlo_list'))
        else:
            return create_api_response(
                status_code=status.HTTP_201_CREATED,
                message=message,
            )
