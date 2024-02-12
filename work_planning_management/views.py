from django.shortcuts import redirect, render, get_object_or_404,HttpResponse
from django.urls import reverse
from django.contrib import messages
from decimal import Decimal
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.views import View
from rest_framework.response import Response
from rest_framework import generics, permissions, filters, status, renderers
from rest_framework.renderers import TemplateHTMLRenderer, JSONRenderer
from rest_framework.status import HTTP_201_CREATED, HTTP_400_BAD_REQUEST
from rest_framework.request import Request

import json
from drf_yasg.utils import swagger_auto_schema

from requirement_management.models import Requirement, Quotation,RequirementDefect
from .serializers import QuotationSerializer, ConvertSTWToFRASerializer, STWDefectSerializer, ConvertSTWDefectsToFRADefectsSerializer, STWDefectsDetailedSerializer, STWRequirementDetailsSerializer
from requirement_management.serializers  import RequirementAddSerializer,RequirementDefectAddSerializer,RequirementAssetSerializer

from infinity_fire_solutions.response_schemas import create_api_response, convert_serializer_errors, render_html_response
from infinity_fire_solutions.aws_helper import *
from infinity_fire_solutions.permission import *
from infinity_fire_solutions.utils import docs_schema_response_new

from .models import *
from .serializers import STWRequirementSerializer, CustomerSerializer, STWDefectSerializer, JobListSerializer,AddJobSerializer,MemberSerializer,TeamSerializer,JobAssignmentSerializer,EventSerializer,STWJobListSerializer, JobCreateSerializer, MemberCalendarSerializer, AttachSitePackSerializer, AddAndAttachSitePackSerializer, CreateRLOSeirlaizer, UpdateRLOSeirlaizer

from requirement_management.serializers import SORSerializer,RequirementDefectSerializer,RequirementDefectAddSerializer
from requirement_management.models import SORItem
from django.http.response import JsonResponse
from django.db import IntegrityError

from datetime import datetime
from .site_pack_views import SitePackJobSerializer

from django.views.generic.detail import DetailView
from django.urls import reverse
from django.utils import timezone
import datetime
from urllib.parse import quote

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import (
    Http404,
    HttpResponseBadRequest,
    HttpResponseRedirect,
    JsonResponse,
)
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import FileResponse

from infinity_fire_solutions.aws_helper import generate_presigned_url

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

class ApprovedQuotationCustomerListView(CustomAuthenticationMixin, generics.ListAPIView):
    
    """
    View for listing stw Requirement customers.

    This view lists Quotation customers, optionally filtered and searchable.
    It provides both HTML and JSON rendering.

    Attributes:
        serializer_class : The serializer class.
        renderer_classes (list): The renderer classes for HTML and JSON.
        filter_backends (list): The filter backends, including search filter.
        search_fields (list): The fields for search.
        template_name (str): The template name for HTML rendering.
        ordering_fields (list): The fields for ordering.
    """

    serializer_class = CustomerSerializer
    renderer_classes = [TemplateHTMLRenderer,JSONRenderer]
    filter_backends = [filters.SearchFilter]
    search_fields = ['first_name', 'last_name', 'company_name', 'email']
    template_name = 'quote_customer_list.html'
    ordering_fields = ['created_at'] 

    def get_queryset(self):
            """
        Get the queryset of stw Requirement customers.

        Returns:
            QuerySet: A queryset of stw Requirement customers.
        """
            queryset = User.objects.filter(is_active=True,  roles__name__icontains='customer').exclude(pk=self.request.user.id)
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
        queryset = self.get_searched_queryset(queryset)
        all_quotes = Quotation.objects.filter(status="approved")
        
        customers_with_counts = []  # Create a list to store customer objects with counts

        for customer in queryset:
            quote_counts = all_quotes.filter(customer_id=customer).count()
            customers_with_counts.append({'customer': customer, 'quote_counts': quote_counts})


        if request.accepted_renderer.format == 'html':
            context = {
                'customers_with_counts': self.get_paginated_queryset(customers_with_counts),
                'search_fields': ['name', 'email','company name'],
                'search_value': request.query_params.get('q', '') if isinstance(request.query_params.get('q', []), str) else ', '.join(request.query_params.get('q', [])),
            }  # Pass the list of customers with counts to the template
            return render_html_response(context, self.template_name)
        else:
            serializer = self.serializer_class(queryset, many=True)
            return create_api_response(status_code=status.HTTP_200_OK,
                                    message="Data retrieved",
                                    data=serializer.data)
    
class ApprovedQuotationListView(CustomAuthenticationMixin, generics.ListAPIView):
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    serializer_class = QuotationSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['requirement_id__action', 'requirement_id__description']
    template_name = 'approved_quotation_list.html'

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
    
    def get_queryset(self):
        exclude_job_quote = self.request.query_params.get('exclude', False)

        customer_id = self.kwargs.get('customer_id') 
        queryset = Quotation.objects.filter(status="approved")
        if customer_id:
            queryset = queryset.filter(customer_id=customer_id)
            if exclude_job_quote:
                queryset = queryset.exclude(id__in=[quote.id for quote in queryset if quote.job_set.first()])
        
        if queryset:
            filters = {
                'surveyor': self.request.GET.get('surveyor'),
                'dateRange': self.request.GET.get('dateRange'),
            }
            date_format = '%d/%m/%Y'

            # Apply additional filters based on the received parameters
            for filter_name, filter_value in filters.items():
                if filter_value:
                    if filter_name == 'dateRange':
                        # If 'dateRange' parameter is provided, filter TODO items within the date range
                        start_date_str, end_date_str = filter_value.split('-')
                        start_date = datetime.datetime.strptime(start_date_str.strip(), date_format).date()
                        end_date = datetime.datetime.strptime(end_date_str.strip(), date_format).date()
                        queryset = queryset.filter(created_at__gte=start_date, created_at__lte=end_date)
                    elif filter_name == 'surveyor':
                        value_list = filter_value.split()
                        if 2 >= len(value_list) > 1:
                            queryset = queryset.filter(requirement_id__surveyor__first_name=value_list[0], requirement_id__surveyor__last_name=value_list[1])
                        else:
                            queryset = queryset.filter(requirement_id__surveyor__first_name = filter_value)

        return queryset
    
    def get(self, request, *args, **kwargs):
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self, "survey", HasListDataPermission, 'list'
        )
        
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect
        
        queryset = self.get_queryset()
        queryset = self.get_searched_queryset(queryset)
        customer_id = self.kwargs.get('customer_id')
        customer_data = get_customer_data(customer_id)
        if not customer_data:
            messages.error(request, "You are not authorized to perform this action")
            return redirect(reverse('approved_quotation_view'))
        
        if request.accepted_renderer.format == 'html':
            context = {
                'approved_quotation': self.get_paginated_queryset(queryset),
                'customer_id': customer_id,
                'customer_data': customer_data,
                'exclude': self.request.query_params.get('exclude', False),
                'search_fields': self.search_fields,
                'search_value': request.query_params.get('q', '') if isinstance(request.query_params.get('q', []), str) else ', '.join(request.query_params.get('q', [])),
            }
            return render(request, self.template_name, context)
        else:
            messages.error(request, "You are not authorized to perform this action")
            return Response(status=status.HTTP_403_FORBIDDEN)

def get_selected_defect_data(request, customer_id, pk):
    """
    Get selected defect data based on the customer and STW requirement.

    This function retrieves selected STW RequirementDefect objects related to the specified customer and STW requirement.

    Args:
        request (HttpRequest): The HTTP request object.
        customer_id (int): The ID of the customer.
        pk (int): The ID of the STW requirement.

    Returns:
        JsonResponse: A JSON response containing selected defect data.
    """
    if request.method == 'POST':
        selected_defect_ids = request.POST.getlist('selectedDefectIds')
        # Query STW RequirementDefect objects related to the customer and STW requirement
        stw_defect = STWDefect.objects.filter(
            stw_id=pk, requirement_id__customer_id=customer_id, pk__in =selected_defect_ids
        )

        # Create a list to store serialized defect data
        defect_data = []

        from django.core import serializers


        for defect in stw_defect:
            # Serialize the defect data (excluding images)
            defect_json = serializers.serialize('json', [defect])
            
            defect_data.append({
                'defect': defect_json,  # Assuming 'defect_json' is a list with one item
            })

        # Create a JSON response containing all the defect data
        response_data = {'defects': defect_data}
        return JsonResponse(response_data, safe=False)

def stw_requirement_image(stw_instance):
    """
    Get document paths and types (image or video) associated with a STW requirement.

    This function retrieves document paths and types (image or video) associated with a given STW requirement.

    Args:
        stw_instance (STWRequirement): The STW Requirement instance.

    Returns:
        list: A list of dictionaries containing document paths and types.
    """
    document_paths = []
    
    for document in STWAsset.objects.filter(stw_id=stw_instance):
        extension = document.document_path.split('.')[-1].lower()

        # is_video = extension in ['mp4', 'avi', 'mov']  # Add more video extensions if needed
        # Remove video upload feature for no support in PDF
        is_video = False
        is_image = extension in ['jpg', 'jpeg', 'png', 'gif']  # Add more image extensions if needed
        document_paths.append({
            'presigned_url': generate_presigned_url(document.document_path),
            'filename': document.document_path,
            'id': document.id,
            'is_video': is_video,
            'is_image': is_image
        })
    return document_paths   

def filter_requirements(data_access_value, user, customer=None, request=None):
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

    if isinstance(request, Request):
        # Get the filtering parameters from the request's query parameters
        filters = {
            'dateRange': request.GET.get('dateRange'),
        }
        date_format = '%d/%m/%Y'

        # Apply additional filters based on the received parameters
        for filter_name, filter_value in filters.items():
            if filter_value:
                if filter_name == 'dateRange':
                    # If 'dateRange' parameter is provided, filter TODO items within the date range
                    start_date_str, end_date_str = filter_value.split('-')
                    start_date = datetime.datetime.strptime(start_date_str.strip(), date_format).date()
                    end_date = datetime.datetime.strptime(end_date_str.strip(), date_format).date()
                    queryset = queryset.filter(created_at__date__gte=start_date, created_at__date__lte=end_date)
                else:
                    # For other filters, apply the corresponding filters on the queryset
                    filter_mapping = {
                        'status': 'status',
                    }
                    queryset = queryset.filter(**{filter_mapping[filter_name]: filter_value.strip()})

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
    search_fields = ['first_name', 'last_name', 'company_name', 'email']
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
        queryset = self.get_searched_queryset(queryset)
        all_stw = STWRequirements.objects.filter()
        
        customers_with_counts = []  # Create a list to store customer objects with counts

        for customer in queryset:
            stw_counts = all_stw.filter(customer_id=customer).count()
            customers_with_counts.append({'customer': customer, 'stw_counts': stw_counts})

        if request.accepted_renderer.format == 'html':
            context = {'customers_with_counts': self.get_paginated_queryset(customers_with_counts),
                'search_fields': ['name', 'email','company name'],
                'search_value': request.query_params.get('q', '') if isinstance(request.query_params.get('q', []), str) else ', '.join(request.query_params.get('q', []))
                }  # Pass the list of customers with counts to the template
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
    search_fields = ['action', 'description','job_number','UPRN']
    template_name = 'stw_list.html'
    ordering_fields = ['created_at'] 
    queryset = STWRequirements.objects.all()

    common_get_response = {
    status.HTTP_200_OK: 
        docs_schema_response_new(
            status_code=status.HTTP_200_OK,
            serializer_class=serializer_class,
            message = "Data retrieved",
            )
    }

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
    
    def get_filtered_queryset(self, queryset):
        # Get the filtering parameters from the request's query parameters
        filters = {
            'dateRange': self.request.GET.get('dateRange'),
        }
        date_format = '%d/%m/%Y'

        # Apply additional filters based on the received parameters
        for filter_name, filter_value in filters.items():
            if filter_value:
                if filter_name == 'dateRange':
                    # If 'dateRange' parameter is provided, filter TODO items within the date range
                    start_date_str, end_date_str = filter_value.split('-')
                    start_date = datetime.datetime.strptime(start_date_str.strip(), date_format).date()
                    end_date = datetime.datetime.strptime(end_date_str.strip(), date_format).date()
                    queryset = queryset.filter(created_at__date__gte=start_date, created_at__date__lte=end_date)
                else:
                    # For other filters, apply the corresponding filters on the queryset
                    filter_mapping = {
                        'status': 'status',
                    }
                    queryset = queryset.filter(**{filter_mapping[filter_name]: filter_value.strip()})
        
        return queryset

    def get_queryset(self, customer_data):
        """
        Get the queryset based on filtering parameters from the request.
        """

        if customer_data:
            queryset = super().get_queryset()
            queryset = queryset.filter(
                customer_id=customer_data
            ).all()

            # Order the queryset based on the 'ordering_fields'
            ordering = self.request.GET.get('ordering')
            if ordering in self.ordering_fields:
                queryset = queryset.order_by(ordering)
            
            queryset = queryset.order_by('-created_at')
            queryset = self.get_filtered_queryset(queryset)
            queryset = self.get_searched_queryset(queryset)

            return queryset

        return None
    
    @swagger_auto_schema(operation_id='STW Requirement Listing', responses={**common_get_response})
    def get(self, request, *args, **kwargs):

        """
        Handle both AJAX (JSON) and HTML requests.
        """
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self, "survey", HasListDataPermission, 'list'
        )
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user
        
        customer_id = self.kwargs.get('customer_id', None)
        customer_data = get_customer_data(customer_id)
        
        if customer_data:
            queryset = self.get_queryset(customer_data)

            if request.accepted_renderer.format == 'html':
                context = {
                    'stw_requirements': self.get_paginated_queryset(queryset), 
                    'customer_id':customer_id,
                    'customer_data':customer_data,
                    'search_fields': self.search_fields,
                    'search_value': request.query_params.get('q', '') if isinstance(request.query_params.get('q', []), str) else ', '.join(request.query_params.get('q', [])),
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
            
            message = "Your STW Requirement has been added successfully."
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
    queryset = STWRequirements.objects.all()

    def get_queryset(self, customer_data):
        """
        Get the queryset based on filtering parameters from the request.
        """
        pk = self.kwargs.get('pk', None)

        if customer_data and pk:
            queryset = super().get_queryset()
            queryset = queryset.filter(
                customer_id=customer_data,
                id=pk
            ).first()

            return queryset

        return None

    @swagger_auto_schema(auto_schema=None)
    def get(self, request, *args, **kwargs):
        # Get the model class using the provided module_name string
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self, "survey", HasUpdateDataPermission, 'change'
        )
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect
        
        customer_id = self.kwargs.get('customer_id')
        customer_data = get_customer_data(customer_id)
        # This method handles GET requests for updating an existing STW Requirement object.
        if customer_data:
            instance = self.get_queryset(customer_data)
            if request.accepted_renderer.format == 'html':
                if instance:
                    serializer = self.serializer_class(instance=instance, context={'request': request})
                    context = {'serializer': serializer, 'stw_instance': instance, 
                            'customer_id': self.kwargs.get('customer_id'),
                            'customer_data':customer_data}
                    return render_html_response(context, self.template_name)
                else:
                    messages.error(request, "You are not authorized to perform this action")
                    return redirect(reverse('customer_stw_list', kwargs={'customer_id': kwargs.get('customer_id')}))
        else:
            messages.error(request, "You are not authorized to perform this action")
            return redirect(reverse('customer_stw_list', kwargs={'customer_id': customer_id})) 
    
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

        customer_id = self.kwargs.get('customer_id')
        customer_data = get_customer_data(customer_id)
        # This method handles GET requests for updating an existing STW Requirement object.
        if customer_data:
            instance = self.get_queryset(customer_data)
            if instance:
                data = request.data
        
                file_list = data.getlist('file_list', [])
                
                if not any(file_list):
                    data = data.copy()      # make a mutable copy of data before performing delete.
                    del data['file_list']
                
                serializer_data = request.data if any(file_list) else data
                serializer_data['job_number'] = instance.job_number
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
        else:
            messages.error(request, "You are not authorized to perform this action")
            return redirect(reverse('customer_stw_list', kwargs={'customer_id': customer_id})) 
            
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
        queryset = STWRequirements.objects.filter(filter_mapping.get(data_access_value, Q()), pk=self.kwargs.get('pk'))
        
        stw_instance = queryset.first()
        print(stw_instance)

        if stw_instance:
            # Proceed with the deletion
            stw_instance.delete()
            messages.success(request, "Your STW requirement has been deleted successfully!")
            return create_api_response(status_code=status.HTTP_404_NOT_FOUND,
                                        message="Your STW requirement has been deleted successfully!", )
        else:
            messages.error(request, "STW Requirement not found OR You are not authorized to perform this action.")
            return create_api_response(status_code=status.HTTP_404_NOT_FOUND,
                                        message="STW Requirement not found OR You are not authorized to perform this action.", )

class ConvertToFRAView(CustomAuthenticationMixin, generics.UpdateAPIView):
    serializer_class = STWRequirementDetailsSerializer
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    swagger_schema = None
    queryset = STWRequirements.objects.all()
    customer = None


    def get_queryset(self) -> STWRequirements:
        """
        Get the queryset for listing STW Requirement items.
        Returns:
            QuerySet: A queryset of STW Requirements items filtered based on the authenticated user's ID.
        """
        # Extract customer_id from kwargs
        pk = self.kwargs.get('pk')
        customer_id = self.kwargs.get('customer_id', None)
        queryset = None
        
        if customer_id and pk:
            queryset = super().get_queryset()
            queryset = queryset.filter(id=pk, customer_id=customer_id).first()
            
            if queryset.job_set.all():
                return None

        return queryset

    def convert_and_attach_defects_to_fra(self, stw_instance: STWRequirements, fra_instance: Requirement):

        stw_defects = STWDefect.objects.filter(stw_id=stw_instance).all()
        if not stw_defects:
            return True, []

        serializer = STWDefectsDetailedSerializer(instance=stw_defects, many=True)
        convert_defect_serializer = ConvertSTWDefectsToFRADefectsSerializer(data=serializer.data, many=True)
        if convert_defect_serializer.is_valid():
            fra_defects = convert_defect_serializer.save(requirement_id=fra_instance)
            stw_defects.delete()
            return True, []
        
        return False, convert_defect_serializer.errors

    def get(self, request, *args, **kwargs):
        """
        Handle GET request to display a form for adding a STW requirement.
        If the STW requirement exists, retrieve the serialized data and render the HTML template.
        If the STW requirement does not exist, render the HTML template with an empty serializer.http://127.0.0.1:8000/work_planning/7/convert-to-fra/1/
        """
        # Get the model class using the provided module_name string
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self, "survey", HasUpdateDataPermission, 'change'
        )
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect
        
        customer_id = kwargs.get('customer_id', None)
        instance = self.get_queryset()
        if not instance:
            messages.error(request, 'You are not authorised to perform this operation')
            return redirect(reverse('customer_stw_list', kwargs={'customer_id': customer_id}))

        self.customer = instance.customer_id
        stw_requirements_serializer = self.get_serializer(instance=instance)
        convert_stw_to_fra_serializer = ConvertSTWToFRASerializer(data=stw_requirements_serializer.data)
        if convert_stw_to_fra_serializer.is_valid():
            try:
                fra_requirement: Requirement = convert_stw_to_fra_serializer.save(user_id=request.user, customer_id=self.customer)

                defectCreated, defectErrors = self.convert_and_attach_defects_to_fra(instance, fra_requirement)
                if not defectCreated and defectErrors:
                    fra_requirement.delete()
                    messages.error(request, 'Unable to validate the STW Defects data to convert it to a FRA Defects, aborting the converstion.')
                    return redirect(reverse('customer_stw_list', kwargs={'customer_id': customer_id}))

                instance.delete()
                messages.success(request, 'STW Successfully Converted to the FRA.')
                return redirect(reverse('customer_requirement_list', kwargs={'customer_id': customer_id}))
            
            except Exception as e:
                messages.error(request, 'Something went wrong while converting the to FRA, please try again later.')
                return redirect(reverse('customer_stw_list', kwargs={'customer_id': customer_id}))

        messages.error(request, 'Unable to validate the STW data to convert it to a FRA.')
        return redirect(reverse('customer_stw_list', kwargs={'customer_id': customer_id}))

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
    template_name = 'stw_details.html'
    serializer_class = STWRequirementSerializer
    queryset = STWRequirements.objects.all()

    def get_queryset(self, customer_data):
        """
        Get the queryset based on filtering parameters from the request.
        """
        pk = self.kwargs.get('pk', None)

        if customer_data and pk:
            queryset = super().get_queryset()
            queryset = queryset.filter(
                customer_id=customer_data,
                id=pk
            ).first()

            return queryset

        return None
    
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
    

    @swagger_auto_schema(auto_schema=None)
    def get(self, request, *args, **kwargs):
        """
        Handle GET requests for displaying STW Requirement details.

        Args:
            request (HttpRequest): The HTTP request object.

        Returns:
            HttpResponse: The response, either HTML or JSON.
        """
        # Get the model class using the provided module_name string
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self, "survey", HasViewDataPermission, 'view'
        )
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect


        customer_id = kwargs.get('customer_id')
        customer_data = User.objects.filter(id=customer_id).first()
        
        if customer_data:
            instance = self.get_queryset(customer_data)
            if not instance:
                messages.error(request, "You are not authorized to perform this action")
                return redirect(reverse('customer_stw_list', kwargs={'customer_id': kwargs.get('customer_id')}))

            # This method handles GET requests for updating an existing STW Requirement object.
            if request.accepted_renderer.format == 'html':
                document_paths = []
                stw_defect = STWDefect.objects.filter(stw_id=instance.id)
                serializer = self.serializer_class(instance=instance, context={'request': request})
                document_paths = stw_requirement_image(instance)
                context = {
                    'serializer': serializer, 
                    'stw_instance': instance, 
                    'stw_defect': self.get_paginated_queryset(stw_defect),
                    'document_paths': document_paths,
                    'customer_id': kwargs.get('customer_id'),
                    'customer_data':customer_data
                    }
                return render_html_response(context, self.template_name)

        messages.error(request, "You are not authorized to perform this action")
        return redirect(reverse('stw_customers_list'))
            
 # Custom JSON encoder that can handle Decimal instances           
class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)  # Convert Decimal to a string
        return super(DecimalEncoder, self).default(obj)
               
class STWDefectView(CustomAuthenticationMixin, generics.CreateAPIView):
    """
    View for adding  a STW requirement.
    Supports both HTML and JSON response formats.
    """
    # serializer_class = RequirementDefectAddSerializer
    serializer_class = STWDefectSerializer
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'stw_defects.html'
    swagger_schema = None
    
    def get_queryset(self):
        """
        Get the filtered queryset for stw requirements based on the authenticated user.
        """
        authenticated_user, data_access_value = check_authentication_and_permissions(
           self,"survey", HasCreateDataPermission, 'view'
        )
        
        queryset = filter_requirements(data_access_value, self.request.user, self.kwargs.get('customer_id'))
        queryset = queryset.filter(pk=self.kwargs.get('stw_id')).first()
        
        return queryset

    
    def get_queryset_defect(self):
        """
        Get the filtered queryset for stw requirements based on the authenticated user.
        """
        queryset_defect = STWDefect.objects.filter(stw_id = self.get_queryset() ).order_by('-created_at')
        return queryset_defect
    
    def get(self, request, *args, **kwargs):
        customer_id = kwargs.get('customer_id')
        customer_data = User.objects.filter(id=customer_id).first()
        # This method handles GET requests for updating an existing stw Requirement object.
        stw_instance = self.get_queryset()
        document_paths = stw_requirement_image(stw_instance)
        
        stw_defects = self.get_queryset_defect()
        defect_instance = stw_defects.filter(pk=self.kwargs.get('pk')).first()
        
        if defect_instance:
            serializer =  self.serializer_class(instance=defect_instance)
            
        else:
            serializer =  self.serializer_class()
            defect_instance = {}

        # Fetch all SOR items and serialize them
        all_sors = SORItem.objects.filter(customer_id=customer_data).values('id', 'name', 'reference_number', 'category_id__name', 'price',)
        all_sors_list = list(all_sors)
        all_sors_json = json.dumps(all_sors_list, cls=DecimalEncoder)
        
        if request.accepted_renderer.format == 'html':
            context = {
                'serializer': serializer,
                'stw_instance': stw_instance,
                'defects_list': self.get_queryset_defect(),
                'defect_instance':defect_instance,
                'customer_id': kwargs.get('customer_id'),
                'document_paths':document_paths,
                'all_sors': all_sors_json,  # Include SOR data in the context
                }
            return render_html_response(context, self.template_name)
        else:
            messages.error(request, "You are not authorized to perform this action")
            return redirect(reverse('customer_stw_list', kwargs={'customer_id': kwargs.get('customer_id')}))  
    
        
    def post(self, request, *args, **kwargs):
        """
        Handle POST request to add a  STW requirement.
        """
        # Call the handle_unauthenticated method to handle unauthenticated access.
        
        data = request.data
        
        file_list = data.getlist('file_list', [])
        
        stw_instance = self.get_queryset()
        defect_instance = STWDefect.objects.filter(stw_id = stw_instance, pk=self.kwargs.get('pk')).first()
        
        if not any(file_list):
            data = data.copy()      # make a mutable copy of data before performing delete.
            del data['file_list']

        # Handle adding SOR items to the defect
        selected_sor_ids = request.POST.getlist('selected_sor_ids[]')
        if defect_instance and selected_sor_ids:
            self.add_sor_to_defect(defect_instance, selected_sor_ids)
        
        serializer_data = request.data if any(file_list) else data
        
        message = "Your  STW requirement defect has been added successfully."
        
        # Check if the site address instance exists for the customer
        if defect_instance:
            # If the site address instance exists, update it.
            serializer = self.serializer_class(data=serializer_data, instance=defect_instance, context={'request': request})
            message = "Your STW requirement defect has been updated successfully!"
        else: 
            # If the site address instance does not exist, create a new one.
            serializer = self.serializer_class(data=serializer_data, context={'request': request})
            message = "Your STW requirement defect has been added successfully!"
        
        
        if serializer.is_valid():
            if  not defect_instance:
                serializer.validated_data['stw_id'] = stw_instance
                serializer.save()
            else:
                serializer.update(defect_instance, validated_data=serializer.validated_data)

            if request.accepted_renderer.format == 'html':
                messages.success(request, message)
                return redirect(reverse('customer_stw_view', kwargs={'customer_id': self.kwargs.get('customer_id'), 'pk':stw_instance.id}))
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
                           'stw_instance': stw_instance,
                           'defects_list': self.get_queryset_defect(),
                        'defect_instance':defect_instance,
                        'customer_id':self.kwargs.get('customer_id')
                           }
                return render_html_response(context,self.template_name)
            else:   
                # Return JSON response with error message.
                return create_api_response(status_code=status.HTTP_400_BAD_REQUEST,
                                    message="We apologize for the inconvenience, but please review the below information.",
                                    data=convert_serializer_errors(serializer.errors))
            

class STWDefectDeleteView(CustomAuthenticationMixin, generics.DestroyAPIView):
    """
    View for deleting a stw defect.
    Supports both HTML and JSON response formats.
    """
    serializer_class = STWDefectSerializer
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    # permission_classes = [IsAuthenticated]
    template_name = 'stw_defects.html'
    swagger_schema = None
    
    def delete(self, request, *args, **kwargs):
        """
        Handle DELETE request to delete a stw defect.
        """
        # Get the stw defect instance from the database
        # Call the handle_unauthenticated method to handle unauthenticated access

        authenticated_user, data_access_value = check_authentication_and_permissions(
            self,"survey", HasDeleteDataPermission, 'delete'
        )
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect
        # Define a mapping of data access values to corresponding filters
        filter_mapping = {
            "self": Q(requirement_id__user_id=request.user ),
            "all": Q(),  # An empty Q() object returns all data
        }

        # Get the appropriate filter from the mapping based on the data access value,
        # or use an empty Q() object if the value is not in the mapping

        queryset = STWDefect.objects.filter(filter_mapping.get(data_access_value, Q()), pk=self.kwargs.get('pk'))
        
        stw_defect = queryset.first()
        
        if stw_defect:
            # Proceed with the deletion
            stw_defect.delete()
            messages.success(request, "STW defect has been deleted successfully!")
            return create_api_response(status_code=status.HTTP_404_NOT_FOUND,
                                        message="Your STW defect has been deleted successfully!", )
        else:
            messages.error(request, "STW defect not found OR You are not authorized to perform this action.")
            return create_api_response(status_code=status.HTTP_404_NOT_FOUND,
                                        message="STW defect not found OR You are not authorized to perform this action.", )
  
class STWDefectRemoveDocumentView(generics.DestroyAPIView):
    """
    View to remove a document associated with a STW defect.
    """
    swagger_schema = None
    
    def destroy(self, request, *args, **kwargs):
        """
        Handles DELETE request to remove the document associated with a STW defect.
        """
        defect_id = kwargs.get('defect_id')
        if defect_id:
            defect_instance = STWDefectDocument.objects.filter(defect_id=defect_id, pk=kwargs.get('pk') ).get()
            if defect_instance and defect_instance.document_path: 
                
                s3_client.delete_object(Bucket=settings.AWS_BUCKET_NAME, Key = defect_instance.document_path)
                defect_instance.delete()
            return Response(
                {"message": "Your STW defect has been deleted successfully."},
                status=status.HTTP_204_NO_CONTENT
            )
        else:
            return Response(
                {"message": "STW Defect not found OR you don't have permission to delete."},
                status=status.HTTP_404_NOT_FOUND
            )
        
class STWDefectDetailView(CustomAuthenticationMixin, generics.CreateAPIView):
    """
    View for displaying and handling stw Defect details.

    This view displays the details of a stw Defect and handles related documents and actions.
    It provides both HTML and JSON rendering.

    Attributes:
        renderer_classes (list): The renderer classes for HTML and JSON.
        template_name (str): The template name for HTML rendering.
        swagger_schema: None
    """

    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'stw_defect_details.html'
    swagger_schema = None
    
    def get_queryset(self):
        """
        Get the filtered queryset for stw defect based on the authenticated user.
        """
        queryset = STWDefect.objects.filter(pk=self.kwargs.get('defect_id')).order_by('-created_at')
        return queryset

    def get_stw_instance(self):
        """
        Get the filtered queryset for stw based on the authenticated user.
        """
        authenticated_user, data_access_value = check_authentication_and_permissions(
           self,"survey", HasCreateDataPermission, 'view'
        )
        
        queryset = filter_requirements(data_access_value, self.request.user, self.kwargs.get('customer_id'))
        queryset = queryset.filter(pk=self.kwargs.get('stw_id')).first()
        
        return queryset

    def get_documents(self):
        """
        Get the filtered document_paths related to the stw Defect.

        Returns:
            list: A list of document paths with additional information (e.g., video/image flags).
        """
        document_paths = []
        
        defect_instance = self.get_queryset().first()
        for document in STWDefectDocument.objects.filter(defect_id=defect_instance):
                extension = document.document_path.split('.')[-1].lower()

                is_video = extension in ['mp4', 'avi', 'mov']  # Add more video extensions if needed
                is_image = extension in ['jpg', 'jpeg', 'png', 'gif']  # Add more image extensions if needed
                
                document_paths.append({
                    'presigned_url': generate_presigned_url(document.document_path),
                    'filename': document.document_path,
                    'id': document.id,
                    'is_video': is_video,
                    'is_image': is_image
                })
        return document_paths

    
    
    @swagger_auto_schema(auto_schema=None)
    def get(self, request, *args, **kwargs):
        """
        Handle GET requests for displaying stw Defect details.

        Args:
            request (HttpRequest): The HTTP request object.
            *args: Variable-length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            HttpResponse: The response, either HTML or JSON.
        """
        customer_id = self.kwargs.get('customer_id')

        customer_data = User.objects.filter(id=customer_id).first()
        if customer_data:
            defect_instance = self.get_queryset().first()
            stw_instance = self.get_stw_instance()
            document_paths = stw_requirement_image(stw_instance)
            
            if not defect_instance:
                messages.warning(request, "You are not authorized to perform this action")
                return redirect(reverse('customer_stw_list', kwargs={'customer_id': self.kwargs.get('customer_id')}))  
            
            # Defect response doesn't exist, prepare context for displaying form
            context = {
                'defect_instance': defect_instance,
                'defect_document_paths':self.get_documents(),
                'defect_instance':defect_instance,
                'document_paths':document_paths,
                'customer_id':customer_id,
                'stw_instance':stw_instance,
                'customer_data':customer_data
            }

            return render_html_response(context, self.template_name)
        else:
            messages.warning(request, "You are not authorized to perform this action")
            return redirect(reverse('customer_stw_list', kwargs={'customer_id': self.kwargs.get('customer_id')}))  
        


class STWSORAddView(CustomAuthenticationMixin, generics.CreateAPIView):
    """
    View for adding or updating a SOR.
    Supports both HTML and JSON response formats.
    """
    serializer_class = SORSerializer
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'stw_sor/sor_form.html'

    def get_queryset(self):
        """
        Get the filtered queryset for stw defect based on the authenticated user.
        """
        queryset = STWDefect.objects.filter(pk=self.kwargs.get('defect_id')).order_by('-created_at')
        return queryset

    @swagger_auto_schema(auto_schema=None) 
    def get(self, request, *args, **kwargs):
        """
        Handle GET request to display a form for updating a SOR.
        If the SOR exists, retrieve the serialized data and render the HTML template.
        If the SOR does not exist, render the HTML template with an empty serializer.
        """
        # Call the handle_unauthenticated method to handle unauthenticated access
        customer_id = self.kwargs.get('customer_id')
        authenticated_user, data_access_value = check_authentication_and_permissions(
           self,"survey", HasCreateDataPermission, 'add'
        )
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect
        
        defect_instance = self.get_queryset().first()
        context = {
                'defect_instance': defect_instance,
                'customer_id':customer_id
            }
            
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
        Handle POST request to add a standalone SOR.
        """
        # Check authentication and permissions here if needed

        message = "SOR has been added successfully."

        data = request.data
        print(data)
        # Retrieve the 'file_list' key from the copied data, or use None if it doesn't exist
        file_list = data.getlist('file_list', None)

        if file_list is not None and not any(file_list):
            data = data.copy()
            del data['file_list']  # Remove the 'file_list' key if it's a blank list or None
        serializer = self.serializer_class(data=data)


        if serializer.is_valid():
            print("valid")
            # Assuming you have a method to create the SOR in your serializer
            serializer.validated_data['customer_id'] = User.objects.get(pk=kwargs.get('customer_id'))  # Assign the current user instance.
            serializer.validated_data['user_id'] = request.user
            sor_data = serializer.save()

            # Serialize the SOR data
            serialized_sor_data = SORSerializer(sor_data).data

            # Update the STWDefect model's sor_data field with the added SOR
            defect_id = kwargs.get('defect_id') 
            print(defect_id) # Assuming you have a defect_id in your URL
            try:
                defect = STWDefect.objects.get(pk=defect_id)
                print(defect)
                if defect.sor_data is None:
                    defect.sor_data = [serialized_sor_data]
                else:
                    defect.sor_data.append(serialized_sor_data)
                defect.save()

                if request.accepted_renderer.format == 'html':
                    messages.success(request, message)
                    return redirect(reverse('customer_stw_list', kwargs={'customer_id': self.kwargs.get('customer_id')}))

                else:
                    # Return JSON response with success message and serialized data
                    return create_api_response(status_code=status.HTTP_201_CREATED,
                                               message=message,
                                               data=serializer.data
                                               )
            except STWDefect.DoesNotExist:
                return create_api_response(status_code=status.HTTP_404_NOT_FOUND,
                                           message="Defect not found"
                                           )
        else:
            # Invalid serializer data
            if request.accepted_renderer.format == 'html':
                # Render the HTML template with invalid serializer data
                context = {'serializer': serializer}
                return render_html_response(context, self.template_name)
            else:
                # Return JSON response with error message
                return create_api_response(status_code=status.HTTP_400_BAD_REQUEST,
                                           message="We apologize for the inconvenience, but please review the below information.",
                                           data=convert_serializer_errors(serializer.errors))
            
class SORUpdateView(CustomAuthenticationMixin, generics.UpdateAPIView):
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
    template_name = 'stw_sor/sor_form.html'


    
    def get_queryset(self):
        """
        Get the queryset for listing SOR SORs.

        Returns:
            QuerySet: A queryset of SOR SORs filtered based on the authenticated user's ID.
        """
        
        # Get the model class using the provided module_name string
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self, "survey", HasUpdateDataPermission, 'change'
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
                   
                    context = {'serializer': serializer, 'sor_instance': instance, 'customer_id': customer_id}
                    return render_html_response(context, self.template_name)
                else:
                    messages.error(request, "You are not authorized to perform this action")
                    return redirect(reverse('customer_sor_list', kwargs={'customer_id': kwargs.get('customer_id')}))
        else:
            messages.error(request, "You are not authorized to perform this action")
            return redirect(reverse('customer_sor_list', kwargs={'customer_id': kwargs.get('customer_id')}))
            
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
                    serializer.validated_data['customer_id'] = User.objects.get(pk=kwargs.get('customer_id'))  # Assign the current user instance.
                    serializer.validated_data['user_id'] = request.user
                    sor_data = serializer.save()

                    # Serialize the updated SOR data
                    serialized_sor_data = SORSerializer(sor_data).data

                    # Update the STWDefect model's sor_data field with the updated SOR
                    defect_id = kwargs.get('defect_id')
                    print(defect_id)  # Assuming you have a defect_id in your URL
                    try:
                        defect = STWDefect.objects.get(pk=defect_id)
                        print(defect)
                        if defect.sor_data is None:
                            defect.sor_data = [serialized_sor_data]
                        else:
                            defect.sor_data.append(serialized_sor_data)
                        defect.save()

                        message = "SOR has been updated successfully!"

                        if request.accepted_renderer.format == 'html':
                            # For HTML requests, display a success message and redirect to list_sor.
                            messages.success(request, message)
                            return redirect(reverse('customer_stw_list', kwargs={'customer_id': kwargs.get('customer_id')}))
                        else:
                            # For API requests, return a success response with serialized data.
                            return create_api_response(status_code=status.HTTP_200_OK,
                                                    message=message,
                                                    data=serializer.data
                                                    )
                    except STWDefect.DoesNotExist:
                        return create_api_response(status_code=status.HTTP_404_NOT_FOUND,
                                                message="Defect not found"
                                                )
                else:
                    if request.accepted_renderer.format == 'html':
                        # For HTML requests with invalid data, render the template with error messages.
                        context = {'serializer': serializer, 'sor_instance': instance, 'customer_id': customer_id}
                        return render(request, self.template_name, context)
                    else:
                        # For API requests with invalid data, return an error response with serializer errors.
                        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            else:
                error_message = "SOR not found"
                if request.accepted_renderer.format == 'html':
                    # For HTML requests with no instance, display an error message and redirect to list_sor.
                    messages.error(request, error_message)
                    return redirect(reverse('customer_sor_list', kwargs={'customer_id': kwargs.get('customer_id')}))
                else:
                    # For API requests with no instance, return an error response with an error message.
                    return create_api_response(status_code=status.HTTP_400_BAD_REQUEST,
                                            message=error_message)
        else:
            messages.error(request, "The specified STW does not exist or you are not authorized to view it.")
            return redirect(reverse('stw_list'))
            


class QuoteJobView(CustomAuthenticationMixin, generics.CreateAPIView):

    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'quote_job_view.html'
    serializer_class = JobListSerializer
    
    def get_object(self):

        quote = Quotation.objects.filter(id=self.kwargs.get('qoute_id')).get()
        
        return quote
    
    def get(self, request, *args, **kwargs):
        authenticated_user, data_access_value = check_authentication_and_permissions(
           self, "survey", HasCreateDataPermission, 'add'
        )
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  

        query_object = self.get_object()
        print(query_object)
        if query_object:

            if request.accepted_renderer.format == 'html':
                context = {'query_object': query_object}
                return render(request, self.template_name, context)
            else:
                return create_api_response(
                    status_code=status.HTTP_201_CREATED,
                    message="GET Method Not Allowed",
                )
        else:
            messages.error(request, "You are not authorized to perform this action")
            return redirect(reverse('approved_quotation_view'))
        
    def post(self, request, *args, **kwargs):
        """
        Handle POST request to add or update a job.
        """

        message = "Your job has been added successfully."
        job_data = Quotation.objects.get(id=self.kwargs.get('qoute_id'))

        # Create a serializer instance with the request data
        serializer = JobListSerializer(data=request.data)
        # serializer = self.serializer_class(data=request.data)
        
        if serializer.is_valid():
            # serializer.validated_data['user_id'] = request.user  # Assign the current user instance
            serializer.validated_data['quotation'] = job_data
            serializer.save()

            if request.accepted_renderer.format == 'html':
                messages.success(request, message)
                return redirect(reverse('jobs_list'))

            else:
                # Return JSON response with success message and serialized data
                return create_api_response(status_code=status.HTTP_201_CREATED,
                                    message=message,
                                    data=serializer.data
                                    )
        else:
            # Invalid serializer data
            if request.accepted_renderer.format == 'html':
                context = {'serializer':serializer}
                return render_html_response(context,self.template_name)
            else:   
                return create_api_response(status_code=status.HTTP_400_BAD_REQUEST,
                                    message="We apologize for the inconvenience, but please review the below information.",
                                    data=convert_serializer_errors(serializer.errors))


def filter_job(data_access_value, user, customer=None):
    # Define a base queryset that contains all jobs
    base_queryset = Job.objects.all()

    # Define a mapping of data access values to corresponding filters.
    filter_mapping = {
        "self": Q(stw_job__quotation__user_id=user.id),
        "all": Q(),  # An empty Q() object returns all data.
    }

    if customer:
        # Filter the base queryset based on customer
        base_queryset = base_queryset.filter(stw_job__quotation__customer_id=customer.id)
    
    # Apply the filter based on data_access_value
    queryset = base_queryset.filter(filter_mapping.get(data_access_value, Q()))
    return queryset
class JobsListView(CustomAuthenticationMixin, generics.ListAPIView):
    serializer_class = STWJobListSerializer
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    filter_backends = [filters.SearchFilter]
    search_fields = ['assigned_to_team__members__name', 'assigned_to_member__name']
    template_name = 'job_list.html'
    ordering_fields = ['created_at']
    queryset = Job.objects.all()

    common_get_response = {
        status.HTTP_200_OK: docs_schema_response_new(
            status_code=status.HTTP_200_OK,
            serializer_class=serializer_class,
            message="Data retrieved",
        )
    }

    def get_filtered_queryset(self, queryset):
        # Get the filtering parameters from the request's query parameters
        filters = {
            'status': self.request.GET.get('status'),
            'dateRange': self.request.GET.get('dateRange'),
        }
        date_format = '%d/%m/%Y'

        # Apply additional filters based on the received parameters
        for filter_name, filter_value in filters.items():
            if filter_value:
                if filter_name == 'dateRange':
                    # If 'dateRange' parameter is provided, filter TODO items within the date range
                    start_date_str, end_date_str = filter_value.split('-')
                    start_date = datetime.datetime.strptime(start_date_str.strip(), date_format).date()
                    end_date = datetime.datetime.strptime(end_date_str.strip(), date_format).date()
                    queryset = queryset.filter(
                        Q(start_date__date__gte=start_date, start_date__date__lte=end_date) |
                        Q(end_date__date__lte=end_date, end_date__date__gte=start_date)
                    )
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

    def get_queryset(self, data_access_value, customer_data):
        """
        Get the queryset based on filtering parameters from the request.
        """
        from django.db.models import F
        queryset = super().get_queryset()
        filter_mapping = {
            "self": Q(user_id=self.request.user),
            "all": Q(),
        }
        queryset = queryset.filter(filter_mapping.get(data_access_value, Q())).distinct()
        queryset = queryset.filter(customer_id=customer_data).all()
        # Order the queryset based on the 'ordering_fields'
        ordering = self.request.GET.get('ordering')
        if ordering in self.ordering_fields:
            queryset = queryset.order_by(ordering)

        queryset = self.get_filtered_queryset(queryset)
        queryset = self.get_searched_queryset(queryset.order_by('-created_at'))
        queryset = self.get_paginated_queryset(queryset)

        return queryset

    @swagger_auto_schema(operation_id='STW Job Assignment Listing', responses={**common_get_response})
    def get(self, request, *args, **kwargs):
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self, "survey", HasListDataPermission, 'list'
        )
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user

        customer_id = kwargs.get('customer_id', None)
        customer_data = get_customer_data(customer_id)

        if customer_data:
            queryset = self.get_queryset(data_access_value, customer_data)

            if request.accepted_renderer.format == 'html':
                context = {
                    'jobs': queryset,
                    'customer_data': customer_data,
                    'status_values': Job_STATUS_CHOICES,
                    'search_fields': self.search_fields,
                    'search_value': request.query_params.get('q', '') if isinstance(request.query_params.get('q', []), str) else ', '.join(request.query_params.get('q', [])),
                }
                return render_html_response(context, self.template_name)
            else:
                serializer = self.serializer_class(queryset, many=True)
                return create_api_response(status_code=status.HTTP_200_OK,
                                           message="Data retrieved",
                                           data=serializer.data)
        else:
            messages.error(request, "You are not authorized to perform this action")
            return redirect(reverse('job_customers_list'))

        
class AddJobView(CustomAuthenticationMixin, generics.CreateAPIView):

    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'stw_job_view.html'
    serializer_class = AddJobSerializer
    
    def get_object(self):
        stw = STWRequirements.objects.filter(id=self.kwargs.get('stw_id')).get()
        return stw
    
    
    def get(self, request, *args, **kwargs):
        authenticated_user, data_access_value = check_authentication_and_permissions(
           self, "survey", HasCreateDataPermission, 'add'
        )
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  

        query_object = self.get_object()
        print(query_object)
        if query_object:

            if request.accepted_renderer.format == 'html':
                context = {'query_object': query_object}
                return render(request, self.template_name, context)
            else:
                return create_api_response(
                status_code=status.HTTP_201_CREATED,
                message="GET Method Not Allowed",
            )
        else:
            messages.error(request, "You are not authorized to perform this action")
            return redirect(reverse('stw_customers_list'))
        
        
    def post(self, request, *args, **kwargs):
        """
        Handle POST request to add or update a stw job.
        """

        message = "Your STW Job has been added successfully."
        # Get the STWRequirement object based on the stw_id
        stw_requirement = STWRequirements.objects.get(id=self.kwargs.get('stw_id'))

        # Create a serializer instance with the request data
        serializer = AddJobSerializer(data=request.data)
        
        if serializer.is_valid():
            # Assign the STWRequirement to the STWJob instance
            serializer.validated_data['stw'] = stw_requirement

            serializer.save()

            if request.accepted_renderer.format == 'html':
                messages.success(request, message)
                return redirect(reverse('jobs_list'))

            else:
                # Return JSON response with success message and serialized data
                return create_api_response(status_code=status.HTTP_201_CREATED,
                                    message=message,
                                    data=serializer.data
                                    )
        else:
            # Invalid serializer data
            if request.accepted_renderer.format == 'html':
                context = {'serializer':serializer}
                return render_html_response(context,self.template_name)
            else:   
                return create_api_response(status_code=status.HTTP_400_BAD_REQUEST,
                                    message="We apologize for the inconvenience, but please review the below information.",
                                    data=convert_serializer_errors(serializer.errors))

class JobCustomerListView(CustomAuthenticationMixin,generics.ListAPIView):
    """
    View for listing job Requirement customers.

    This view lists job Requirement customers, optionally filtered and searchable.
    It provides both HTML and JSON rendering.

    Attributes:
        serializer_class (JOBCustomerSerializer): The serializer class.
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
    template_name = 'job_customer_list.html'
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
        all_stw = Quotation.objects.filter(status="approved")
        
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
        

# class JobDeleteView(CustomAuthenticationMixin, generics.DestroyAPIView):
#     """
#     View for deleting a single job.
#     This view provides both HTML and JSON rendering.
#     """

#     renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
#     serializer_class = STWJobListSerializer
#     template_name = 'job_list.html'
#     queryset = Job.objects.filter()

#     def get_queryset(self):
#         job_id = self.kwargs.get('job_id', None)
#         customer_id = self.kwargs.get('customer_id', None)
#         queryset = None

#         if job_id and customer_id:
#             queryset = super().get_queryset()
#             queryset = queryset.filter(
#                 pk = job_id,
#                 customer_id = customer_id
#             ).first()

#         return queryset

#     def get(self, request, *args, **kwargs):
#         authenticated_user, data_access_value = check_authentication_and_permissions(
#             self, "survey", HasListDataPermission, 'list'
#         )
#         if isinstance(authenticated_user, HttpResponseRedirect):
#             return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect
        
#         customer_id = self.kwargs.get('customer_id', None)

#         breakpoint()
#         instance = self.get_queryset()
#         if not instance:
#             messages.error(request, "You are not authorized to perform this action")
#             return redirect(reverse('jobs_list', kwargs={'customer_id': customer_id}))

#         if request.accepted_renderer.format == 'html':
#             context = {'job': job}
#             return render(request, self.template_name, context)
#         else:
#             serializer = self.serializer_class(job)
#             return create_api_response(status_code=status.HTTP_200_OK,
#                                        message="Data retrieved",
#                                        data=serializer.data)

#     def delete(self, request, *args, **kwargs):
#         breakpoint()
#         job_id = self.kwargs.get('job_id')
#         print(job_id)
#         customer_id = self.kwargs.get('customer_id')
#         queryset = self.get_queryset()
#         print(queryset)

#         try:
#             job = queryset.get(id=job_id)
#         except Job.DoesNotExist:
#             return Response(status=status.HTTP_404_NOT_FOUND)

#         # You can add permission checks here to ensure the user has the right to delete the job.

#         job.delete()

#         if request.accepted_renderer.format == 'html':
#             messages.success(request, "Job has been deleted successfully.")
#             return redirect(reverse('job_list'))
#         else:
#             return create_api_response(status_code=status.HTTP_204_NO_CONTENT,
#                                        message="Job deleted successfully.")
        

class JobDetailView(CustomAuthenticationMixin, generics.RetrieveAPIView):
    """
    View for retrieving job details.

    This view retrieves details of a job, optionally filtered and searchable.
    It provides both HTML and JSON rendering.

    Attributes:
        serializer_class (JobSerializer): The serializer class for the job.
        renderer_classes (list): The renderer classes for HTML and JSON.
        template_name (str): The template name for HTML rendering.
    """

    serializer_class = STWJobListSerializer
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'job_detail.html'
    queryset = Job.objects.all()

    def get_queryset(self):
        """
        Get the queryset of jobs.

        Returns:
        QuerySet: A queryset of jobs.
        """
        job_id = self.kwargs.get('job_id', None)
        customer_id = self.kwargs.get('customer_id', None)
        queryset = None

        if job_id and customer_id:
            # Your queryset logic to filter jobs goes here
            queryset = super().get_queryset().filter(id=job_id, customer_id=customer_id).first()

        return queryset

    def get(self, request, *args, **kwargs):
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self, "survey", HasListDataPermission, 'list'
        )
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect
        
        customer_id = self.kwargs.get('customer_id')

        instance = self.get_queryset()
        
        if not instance:
            messages.error(request, "You are not authorized to perform this action")
            return redirect(reverse('jobs_list', kwargs={'customer_id': customer_id}))

        # Additional job data can be retrieved here based on your requirements
        # For example, get related data or perform other queries to obtain additional job details

        if request.accepted_renderer.format == 'html':
            context = {
                'job': instance,
                # Add more job-related data to the context as needed
            }
            return render(request, self.template_name, context)
        else:
            serializer = self.serializer_class(instance)
            return create_api_response(status_code=status.HTTP_200_OK,
                                    message="Data retrieved",
                                    data=serializer.data)

class JobSitePacksDetailView(CustomAuthenticationMixin, generics.GenericAPIView):
    """
    View for retrieving job details.

    This view retrieves details of a job, optionally filtered and searchable.
    It provides both HTML and JSON rendering.

    Attributes:
        serializer_class (JobSerializer): The serializer class for the job.
        renderer_classes (list): The renderer classes for HTML and JSON.
        template_name (str): The template name for HTML rendering.
    """

    serializer_class = AttachSitePackSerializer
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'job_site_packs_detail.html'
    queryset = JobDocument.objects.all()
    
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

    def get_job_instance(self):
        """
        Get the queryset of jobs.

        Returns:
        QuerySet: A queryset of jobs.
        """
        job_id = self.kwargs.get('job_id', None)
        customer_id = self.kwargs.get('customer_id', None)
        queryset = None

        if job_id and customer_id:
            # Your queryset logic to filter jobs goes here
            queryset = Job.objects.filter(id=job_id, customer_id=customer_id).first()

        return queryset

    def get_queryset(self):
        """
        Get the queryset of jobs.

        Returns:
        QuerySet: A queryset of jobs.
        """
        job_id = self.kwargs.get('job_id', None)
        customer_id = self.kwargs.get('customer_id', None)
        queryset = None

        if job_id and customer_id:
            # Your queryset logic to filter jobs goes here
            queryset = super().get_queryset().filter(job=job_id, job__customer_id=customer_id).all()

        return queryset

    def get(self, request, *args, **kwargs):
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self, "survey", HasListDataPermission, 'list'
        )
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect

        customer_id = self.kwargs.get('customer_id')

        instance = self.get_job_instance()
        queryset = self.get_queryset()
        
        if not instance:
            messages.error(request, "You are not authorized to perform this action")
            return redirect(reverse('jobs_list', kwargs={'customer_id': customer_id}))
        # Additional job data can be retrieved here based on your requirements
        # For example, get related data or perform other queries to obtain additional job details

        if request.accepted_renderer.format == 'html':
            context = {
                'job': instance,
                'site_packs': self.get_paginated_queryset(queryset),
                'default_site_packs': SitePack.objects.filter(user_id__is_staff=True).all()
                # Add more job-related data to the context as needed
            }
            return render(request, self.template_name, context)
        else:
            serializer = self.serializer_class(instance)
            return create_api_response(status_code=status.HTTP_200_OK,
                                    message="Data retrieved",
                                    data=serializer.data)
    
    def post(self, request, *args, **kwargs):
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self, "survey", HasListDataPermission, 'list'
        )
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect

        customer_id = self.kwargs.get('customer_id')

        instance = self.get_job_instance()
        queryset = self.get_queryset()
        
        if not instance:
            messages.error(request, "You are not authorized to perform this action.")
            return redirect(reverse('jobs_list', kwargs={'customer_id': customer_id}))

        serializer_data = request.data.copy()
        serializer_class_type = serializer_data.get('type', 'default')
        serializer_data['job'] = instance.id
        
        if serializer_class_type == 'default':
            serializer = self.serializer_class(data=serializer_data)
        elif serializer_class_type == 'new':
            serializer_data['user_id'] = request.user.id
            serializer = AddAndAttachSitePackSerializer(data=serializer_data)
        else:
            messages.error(request, "You are not authorized to perform this action.")
            return redirect(reverse('jobs_list', kwargs={'customer_id': customer_id}))
        
        if serializer.is_valid():
            serializer.save()
            messages.success(request, "Site Pack has been added successfully.")
            if request.accepted_renderer.format == 'html':
                context = {
                    'job': instance,
                    'site_packs': queryset,
                    'default_site_packs': SitePack.objects.filter(user_id__is_staff=True).all()
                    # Add more job-related data to the context as needed
                }
                return render(request, self.template_name, context)
            else:
                serializer = self.serializer_class(instance)
                return create_api_response(status_code=status.HTTP_200_OK,
                                        message="Data retrieved",
                                        data=serializer.data)
        
        if request.accepted_renderer.format == 'html':
            context = {
                'job': instance,
                'site_packs': queryset,
                'default_site_packs': SitePack.objects.filter(user_id__is_staff=True).all(),
                'default_site_packs_erros' if serializer_class_type == 'default' else  'new_site_packs_erros': convert_serializer_errors(serializer.errors)
                # Add more job-related data to the context as needed
            }
            return render(request, self.template_name, context)
        else:
            serializer = self.serializer_class(instance)
            return create_api_response(status_code=status.HTTP_200_OK,
                                    message="Data retrieved",
                                    data=serializer.data)

class JobSitePacksDownloadView(CustomAuthenticationMixin, generics.GenericAPIView):
    """
    View for retrieving job details.

    This view retrieves details of a job, optionally filtered and searchable.
    It provides both HTML and JSON rendering.

    Attributes:
        serializer_class (JobSerializer): The serializer class for the job.
        renderer_classes (list): The renderer classes for HTML and JSON.
        template_name (str): The template name for HTML rendering.
    """

    serializer_class = AddAndAttachSitePackSerializer
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'job_site_packs_detail.html'
    queryset = JobDocument.objects.all()

    def get_job_instance(self):
        """
        Get the queryset of jobs.

        Returns:
        QuerySet: A queryset of jobs.
        """
        job_id = self.kwargs.get('job_id', None)
        customer_id = self.kwargs.get('customer_id', None)
        queryset = None

        if job_id and customer_id:
            # Your queryset logic to filter jobs goes here
            queryset = Job.objects.filter(id=job_id, customer_id=customer_id).first()

        return queryset

    def get_queryset(self):
        """
        Get the queryset of jobs.

        Returns:
        QuerySet: A queryset of jobs.
        """
        job_id = self.kwargs.get('job_id', None)
        customer_id = self.kwargs.get('customer_id', None)
        queryset = None

        if job_id and customer_id:
            # Your queryset logic to filter jobs goes here
            queryset = super().get_queryset().filter(job=job_id, job__customer_id=customer_id).all()

        return queryset

    def get_object(self):
        job = self.get_job_instance()
        queryset = self.get_queryset()
        site_pack_id = self.kwargs.get('site_pack_id', None)

        if queryset and site_pack_id:

            instance = queryset.filter(job=job, id=site_pack_id).first()
            return instance
        
        return None

    def get(self, request, *args, **kwargs):
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self, "survey", HasListDataPermission, 'list'
        )
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect

        customer_id = self.kwargs.get('customer_id')

        instance = self.get_job_instance()
        if not instance:
            messages.error(request, "You are not authorized to perform this action")
            return redirect(reverse('jobs_list', kwargs={'customer_id': customer_id}))

        site_pack_instance = self.get_object()
        if not site_pack_instance:
            messages.error(request, "No site pack found.")
            return redirect(reverse('job_site_packs_detail', kwargs={'customer_id': customer_id, 'job_id': instance.id}))
        
        try:
            document = site_pack_instance.sitepack_document
            presigned_url = generate_presigned_url(f'sitepack_doc/{document.document_path}')
        except:
            messages.error(request, "Something went wromg, please try again later.")
            return redirect(reverse('job_site_packs_detail', kwargs={'customer_id': customer_id, 'job_id': instance.id}))
        
        if request.accepted_renderer.format == 'html':
            messages.success(request, "Site pack downloaded Successfully.")
            return redirect(presigned_url)
        else:
            serializer = self.serializer_class(instance)
            return create_api_response(status_code=status.HTTP_200_OK,
                                    message="Data retrieved",
                                    data=serializer.data)

class JobSitePacksDeleteView(CustomAuthenticationMixin, generics.GenericAPIView):
    """
    View for retrieving job details.

    This view retrieves details of a job, optionally filtered and searchable.
    It provides both HTML and JSON rendering.

    Attributes:
        serializer_class (JobSerializer): The serializer class for the job.
        renderer_classes (list): The renderer classes for HTML and JSON.
        template_name (str): The template name for HTML rendering.
    """

    serializer_class = AddAndAttachSitePackSerializer
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'job_site_packs_detail.html'
    queryset = JobDocument.objects.all()

    def get_job_instance(self):
        """
        Get the queryset of jobs.

        Returns:
        QuerySet: A queryset of jobs.
        """
        job_id = self.kwargs.get('job_id', None)
        customer_id = self.kwargs.get('customer_id', None)
        queryset = None

        if job_id and customer_id:
            # Your queryset logic to filter jobs goes here
            queryset = Job.objects.filter(id=job_id, customer_id=customer_id).first()

        return queryset

    def get_queryset(self):
        """
        Get the queryset of jobs.

        Returns:
        QuerySet: A queryset of jobs.
        """
        job_id = self.kwargs.get('job_id', None)
        customer_id = self.kwargs.get('customer_id', None)
        queryset = None

        if job_id and customer_id:
            # Your queryset logic to filter jobs goes here
            queryset = super().get_queryset().filter(job=job_id, job__customer_id=customer_id).all()

        return queryset

    def get_object(self):
        job = self.get_job_instance()
        queryset = self.get_queryset()
        site_pack_id = self.kwargs.get('site_pack_id', None)

        if queryset and site_pack_id:

            instance = queryset.filter(job=job, id=site_pack_id).first()
            return instance
        
        return None

    def get(self, request, *args, **kwargs):
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self, "survey", HasListDataPermission, 'list'
        )
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect

        customer_id = self.kwargs.get('customer_id')

        instance = self.get_job_instance()
        if not instance:
            messages.error(request, "You are not authorized to perform this action")
            return redirect(reverse('jobs_list', kwargs={'customer_id': customer_id}))

        site_pack_instance = self.get_object()
        if not site_pack_instance:
            messages.error(request, "No site pack found.")
            return redirect(reverse('job_site_packs_detail', kwargs={'customer_id': customer_id, 'job_id': instance.id}))
        
        serializer = self.serializer_class(instance=site_pack_instance)
        serializer.delete(site_pack_instance)

        queryset = self.get_queryset()
        # Additional job data can be retrieved here based on your requirements
        # For example, get related data or perform other queries to obtain additional job details

        if request.accepted_renderer.format == 'html':
            messages.success(request, "Site pack deleted Successfully.")
            return redirect(reverse('job_site_packs_detail', kwargs={'customer_id': customer_id, 'job_id': instance.id}))
        else:
            serializer = self.serializer_class(instance)
            return create_api_response(status_code=status.HTTP_200_OK,
                                    message="Data retrieved",
                                    data=serializer.data)

class JobRLODetailView(CustomAuthenticationMixin, generics.GenericAPIView):
    """
    View for retrieving job details.

    This view retrieves details of a job, optionally filtered and searchable.
    It provides both HTML and JSON rendering.

    Attributes:
        serializer_class (JobSerializer): The serializer class for the job.
        renderer_classes (list): The renderer classes for HTML and JSON.
        template_name (str): The template name for HTML rendering.
    """

    serializer_class = AttachSitePackSerializer
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'job_rlo_detail.html'
    queryset = RLO.objects.all()

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

    def get_job_instance(self):
        """
        Get the queryset of jobs.

        Returns:
        QuerySet: A queryset of jobs.
        """
        job_id = self.kwargs.get('job_id', None)
        customer_id = self.kwargs.get('customer_id', None)
        queryset = None

        if job_id and customer_id:
            # Your queryset logic to filter jobs goes here
            queryset = Job.objects.filter(id=job_id, customer_id=customer_id).first()

        return queryset

    def get_queryset(self):
        """
        Get the queryset of jobs.

        Returns:
        QuerySet: A queryset of jobs.
        """
        job = self.get_job_instance()
        queryset = None

        if job:
            # Your queryset logic to filter jobs goes here
            queryset = super().get_queryset().filter(job=job).all()

        return queryset
    
    def get(self, request, *args, **kwargs):
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self, "survey", HasListDataPermission, 'list'
        )
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect

        customer_id = self.kwargs.get('customer_id')

        instance = self.get_job_instance()
        queryset = self.get_queryset()
        
        if not instance:
            messages.error(request, "You are not authorized to perform this action")
            return redirect(reverse('jobs_list', kwargs={'customer_id': customer_id}))
        # Additional job data can be retrieved here based on your requirements
        # For example, get related data or perform other queries to obtain additional job details

        if request.accepted_renderer.format == 'html':
            context = {
                'job': instance,
                'rlo_list': self.get_paginated_queryset(queryset),
                # Add more job-related data to the context as needed
            }
            return render(request, self.template_name, context)
        else:
            serializer = self.serializer_class(instance)
            return create_api_response(status_code=status.HTTP_200_OK,
                                    message="Data retrieved",
                                    data=serializer.data)

class JobRLOAddView(CustomAuthenticationMixin, generics.CreateAPIView):
    """
    View for adding  a RLO ADD.
    Supports both HTML and JSON response formats.
    """
    serializer_class = CreateRLOSeirlaizer
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'RLO/rlo_form.html'
    queryset = RLOLetterTemplate.objects.all()

    def get_job_instance(self):
        """
        Get the queryset of jobs.

        Returns:
        QuerySet: A queryset of jobs.
        """
        job_id = self.kwargs.get('job_id', None)
        customer_id = self.kwargs.get('customer_id', None)
        queryset = None

        if job_id and customer_id:
            # Your queryset logic to filter jobs goes here
            queryset = Job.objects.filter(id=job_id, customer_id=customer_id).first()

        return queryset

    def get(self, request, *args, **kwargs):
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self, "survey", HasListDataPermission, 'list'
        )
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect

        customer_id = self.kwargs.get('customer_id')

        instance = self.get_job_instance()
        queryset = self.get_queryset()

        if not instance:
            messages.error(request, "You are not authorized to perform this action")
            return redirect(reverse('jobs_list', kwargs={'customer_id': customer_id}))
            
        if request.accepted_renderer.format == 'html':
            context = {
                'default_rlo': queryset,
            }
                
            return render_html_response(context, self.template_name)
        else:
            return create_api_response(status_code=status.HTTP_201_CREATED,
                                    message="GET Method Not Alloweded",)
    
    def post(self, request, *args, **kwargs):
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self, "survey", HasListDataPermission, 'list'
        )
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect
        
        customer_id = self.kwargs.get('customer_id')
        instance = self.get_job_instance()
        queryset = self.get_queryset()

        if not instance:
            messages.error(request, "You are not authorized to perform this action")
            return redirect(reverse('jobs_list', kwargs={'customer_id': customer_id}))

        serializer_data = request.data.copy()
        serializer_data['job'] = instance.id
        serializer = self.serializer_class(data=serializer_data)       
        message = "Your RLO has been added successfully."
        if serializer.is_valid():
            serializer.save(user_id = request.user)

            if request.accepted_renderer.format == 'html':
                messages.success(request, message)
                return redirect(reverse('job_rlo_detail', kwargs={"customer_id": customer_id, "job_id": instance.id}))
            else:
                # Return JSON response with success message and serialized data.
                return create_api_response(
                    status_code=status.HTTP_201_CREATED, 
                    message=message, data=serializer.data
                )

        else:
            if request.accepted_renderer.format == 'html':
                context = {
                    'default_rlo': queryset,
                    'errors': convert_serializer_errors(serializer.errors)
                }
                return render_html_response(context, self.template_name)
            else:
                # Return JSON response with success message and serialized data.
                return create_api_response(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    message="We apologize for the inconvenience, but please review the below information.",
                    data=convert_serializer_errors(serializer.errors)
                )

# class JobRLODownloadView(CustomAuthenticationMixin, generics.CreateAPIView):
#     """
#     View for adding  a RLO ADD.
#     Supports both HTML and JSON response formats.
#     """
#     renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
#     template_name = 'RLO/rlo_pdf.html'
#     queryset = RLO.objects.all()
#     serializer_class = RLOAddSerializer
    
#     pdf_options = {
#         'page-size': 'A4',  # You can change this to 'A4' or custom size
#         'margin-top': '10mm',
#         'margin-right': '0mm',
#         'margin-bottom': '0mm',
#         'margin-left': '0mm',
#     }
#     def save_pdf_from_html(self, context, file_name):
#         """
#         Save the PDF file from the HTML content.
#         Args:
#             context (dict): Context data for rendering the HTML template.
#             file_name (str): Name of the PDF file.
#         Returns:
#             Output file path or None.
#         """
#         output_file = None
#         local_folder = '/tmp'

#         if local_folder:
#             try:
#                 os.makedirs(local_folder, exist_ok=True)
#                 output_file = os.path.join(local_folder, file_name)

#                 # get the html text from the tmplate
#                 html_content = render_to_string('RLO/rlo_pdf.html', context)

#                 # create the PDF file for the invoice
#                 pdfkit.from_string(html_content, output_file, options=self.pdf_options)
                
#             except Exception as e:
#                 # Handle any exceptions that occur during PDF generation
#                 print("error")

#         return output_file


#     def get_job_instance(self):
#         """
#         Get the queryset of jobs.

#         Returns:
#         QuerySet: A queryset of jobs.
#         """
#         job_id = self.kwargs.get('job_id', None)
#         customer_id = self.kwargs.get('customer_id', None)
#         queryset = None

#         if job_id and customer_id:
#             # Your queryset logic to filter jobs goes here
#             queryset = Job.objects.filter(id=job_id, customer_id=customer_id).first()

#         return queryset

#     def get_object(self):
#         job = self.get_job_instance()
#         rlo_id = self.kwargs.get('rlo_id', None)

#         if job:
#             instance = self.get_queryset().filter(job=job, id=rlo_id).first()
#             return instance
        
#         return None
    

#     @swagger_auto_schema(auto_schema=None)
#     def get(self, request, *args, **kwargs):
#         """
#         Handle GET requests for RLO.

#         Args:
#             request (HttpRequest): The HTTP request object.

#         Returns:
#             HttpResponse: The response, either HTML or JSON.
#         """
       
#         authenticated_user, data_access_value = check_authentication_and_permissions(
#             self, "survey", HasListDataPermission, 'list'
#         )
#         if isinstance(authenticated_user, HttpResponseRedirect):
#             return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect

#         customer_id = self.kwargs.get('customer_id')

#         job = self.get_job_instance()
#         instance = self.get_object()

#         if not job:
#             messages.error(request, "You are not authorized to perform this action")
#             return redirect(reverse('jobs_list', kwargs={'customer_id': customer_id}))
        
#         if not instance:
#             messages.success(request, 'No RLO Found.')
#             return redirect(reverse('job_rlo_detail', kwargs={"customer_id": customer_id, "job_id": instance.id}))
        
#         template_content = instance.edited_content
#         serializer = self.serializer_class(instance=instance, context={'request': request})        
#         context = {
#             'serializer': serializer, 
#             'instance': instance, 
#             'template_content': template_content,
#         }
#         if request.accepted_renderer.format == 'html':
#             return render_html_response(context, self.template_name)
#         else:
#             messages.error(request, "You are not authorized to perform this action")
#             return redirect(reverse('job_rlo_detail', kwargs={"customer_id": customer_id, "job_id": instance.id}))


class JobRLODeleteView(CustomAuthenticationMixin, generics.CreateAPIView):
    """
    View for adding  a RLO ADD.
    Supports both HTML and JSON response formats.
    """
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'RLO/rlo_form.html'
    queryset = RLO.objects.all()

    def get_job_instance(self):
        """
        Get the queryset of jobs.

        Returns:
        QuerySet: A queryset of jobs.
        """
        job_id = self.kwargs.get('job_id', None)
        customer_id = self.kwargs.get('customer_id', None)
        queryset = None

        if job_id and customer_id:
            # Your queryset logic to filter jobs goes here
            queryset = Job.objects.filter(id=job_id, customer_id=customer_id).first()

        return queryset

    def get_object(self):
        job = self.get_job_instance()
        rlo_id = self.kwargs.get('rlo_id', None)

        if job:
            instance = self.get_queryset().filter(job=job, id=rlo_id).first()
            return instance
        
        return None


    def get(self, request, *args, **kwargs):
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self, "survey", HasListDataPermission, 'list'
        )
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect

        customer_id = self.kwargs.get('customer_id')

        job = self.get_job_instance()
        instance = self.get_object()

        if not job:
            messages.error(request, "You are not authorized to perform this action")
            return redirect(reverse('jobs_list', kwargs={'customer_id': customer_id}))
        
        if not instance:
            messages.success(request, 'No RLO Found.')
            return redirect(reverse('job_rlo_detail', kwargs={"customer_id": customer_id, "job_id": job.id}))
        
        instance.delete()
            
        if request.accepted_renderer.format == 'html':
                messages.success(request, 'RLO Deleted successfully!')
                return redirect(reverse('job_rlo_detail', kwargs={"customer_id": customer_id, "job_id": job.id}))
        else:
            # Return JSON response with success message and serialized data.
            return create_api_response(
                status_code=status.HTTP_201_CREATED, 
                message='RLO Deleted successfully!'
            )

class JobRLOApproveView(CustomAuthenticationMixin, generics.CreateAPIView):
    """
    View for adding  a RLO ADD.
    Supports both HTML and JSON response formats.
    """
    serializer_class = UpdateRLOSeirlaizer
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'RLO/rlo_form.html'
    queryset = RLO.objects.all()

    def get_job_instance(self):
        """
        Get the queryset of jobs.

        Returns:
        QuerySet: A queryset of jobs.
        """
        job_id = self.kwargs.get('job_id', None)
        customer_id = self.kwargs.get('customer_id', None)
        queryset = None

        if job_id and customer_id:
            # Your queryset logic to filter jobs goes here
            queryset = Job.objects.filter(id=job_id, customer_id=customer_id).first()

        return queryset

    def get_object(self):
        job = self.get_job_instance()
        rlo_id = self.kwargs.get('rlo_id', None)

        if job:
            instance = self.get_queryset().filter(job=job, id=rlo_id).first()
            return instance
        
        return None


    def get(self, request, *args, **kwargs):
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self, "survey", HasListDataPermission, 'list'
        )
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect

        customer_id = self.kwargs.get('customer_id')

        job = self.get_job_instance()
        instance = self.get_object()
        if not job:
            messages.error(request, "You are not authorized to perform this action")
            return redirect(reverse('jobs_list', kwargs={'customer_id': customer_id}))
        
        if not instance:
            messages.success(request, 'No RLO Found.')
            return redirect(reverse('job_rlo_detail', kwargs={"customer_id": customer_id, "job_id": job.id}))
        
        serializer = self.serializer_class(
            data={
                'status': 'approved'
            },
            instance=instance
        )
        if serializer.is_valid():
            serializer.update(instance, serializer.validated_data)
            
            if request.accepted_renderer.format == 'html':
                    messages.success(request, 'RLO Approved successfully!')
                    return redirect(reverse('job_rlo_detail', kwargs={"customer_id": customer_id, "job_id": job.id}))
            else:
                # Return JSON response with success message and serialized data.
                return create_api_response(
                    status_code=status.HTTP_201_CREATED, 
                    message='RLO Approved successfully!'
                )

        if request.accepted_renderer.format == 'html':
                messages.success(request, 'Something Went wrong while approving the RLO please try again later.')
                return redirect(reverse('job_rlo_detail', kwargs={"customer_id": customer_id, "job_id": job.id}))
        else:
            # Return JSON response with success message and serialized data.
            return create_api_response(
                status_code=status.HTTP_201_CREATED, 
                message='Something Went wrong while approving the RLO please try again later.',
                data = convert_serializer_errors(serializer.errors)
            )

class JobRLORejectView(CustomAuthenticationMixin, generics.CreateAPIView):
    """
    View for adding  a RLO ADD.
    Supports both HTML and JSON response formats.
    """
    serializer_class = UpdateRLOSeirlaizer
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'RLO/rlo_form.html'
    queryset = RLO.objects.all()

    def get_job_instance(self):
        """
        Get the queryset of jobs.

        Returns:
        QuerySet: A queryset of jobs.
        """
        job_id = self.kwargs.get('job_id', None)
        customer_id = self.kwargs.get('customer_id', None)
        queryset = None

        if job_id and customer_id:
            # Your queryset logic to filter jobs goes here
            queryset = Job.objects.filter(id=job_id, customer_id=customer_id).first()

        return queryset

    def get_object(self):
        job = self.get_job_instance()
        rlo_id = self.kwargs.get('rlo_id', None)

        if job:
            instance = self.get_queryset().filter(job=job, id=rlo_id).first()
            return instance
        
        return None


    def get(self, request, *args, **kwargs):
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self, "survey", HasListDataPermission, 'list'
        )
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect

        customer_id = self.kwargs.get('customer_id')

        job = self.get_job_instance()
        instance = self.get_object()

        if not job:
            messages.error(request, "You are not authorized to perform this action")
            return redirect(reverse('jobs_list', kwargs={'customer_id': customer_id}))
        
        if not instance:
            messages.success(request, 'No RLO Found.')
            return redirect(reverse('job_rlo_detail', kwargs={"customer_id": customer_id, "job_id": job.id}))
        
        serializer = self.serializer_class(
            data={
                'status': 'rejected'
            },
            instance=instance
        )
        if serializer.is_valid():
            serializer.update(instance, serializer.validated_data)
            
            if request.accepted_renderer.format == 'html':
                    messages.success(request, 'RLO Rejected successfully!')
                    return redirect(reverse('job_rlo_detail', kwargs={"customer_id": customer_id, "job_id": job.id}))
            else:
                # Return JSON response with success message and serialized data.
                return create_api_response(
                    status_code=status.HTTP_201_CREATED, 
                    message='RLO Rejected successfully!'
                )

        if request.accepted_renderer.format == 'html':
                messages.success(request, 'Something Went wrong while rejecting the RLO please try again later.')
                return redirect(reverse('job_rlo_detail', kwargs={"customer_id": customer_id, "job_id": job.id}))
        else:
            # Return JSON response with success message and serialized data.
            return create_api_response(
                status_code=status.HTTP_201_CREATED, 
                message='Something Went wrong while rejecting the RLO please try again later.',
                data = convert_serializer_errors(serializer.errors)
            )

class JobCustomerListView(CustomAuthenticationMixin,generics.ListAPIView):
    """
    View for listing job Requirement customers.
    This view lists job Requirement customers, optionally filtered and searchable.
    It provides both HTML and JSON rendering.
    Attributes:
        serializer_class (JOBCustomerSerializer): The serializer class.
        renderer_classes (list): The renderer classes for HTML and JSON.
        filter_backends (list): The filter backends, including search filter.
        search_fields (list): The fields for search.
        template_name (str): The template name for HTML rendering.
        ordering_fields (list): The fields for ordering.
    """

    serializer_class = CustomerSerializer
    renderer_classes = [TemplateHTMLRenderer,JSONRenderer]
    filter_backends = [filters.SearchFilter]
    search_fields = ['first_name', 'last_name','email','company_name']
    template_name = 'job_customer_list.html'
    ordering_fields = ['created_at'] 

    def get_queryset(self):
            """
        Get the queryset of stw Requirement customers.
        Returns:
            QuerySet: A queryset of stw Requirement customers.
        """
            queryset = User.objects.filter(is_active=True,  roles__name__icontains='customer').exclude(pk=self.request.user.id)
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
        queryset = self.get_searched_queryset(queryset)
        all_quotes = Quotation.objects.filter(status="approved")
        
        customers_with_counts = []  # Create a list to store customer objects with counts

        for customer in queryset:
            quote_counts = all_quotes.filter(customer_id=customer).count()
            customers_with_counts.append({'customer': customer, 'quote_counts': quote_counts})

        if request.accepted_renderer.format == 'html':
            # context = {'customers_with_counts': customers_with_counts,'queryset': self.get_paginated_queryset(queryset)}
            
            context = { 'customers_with_counts': self.get_paginated_queryset(customers_with_counts),
                'search_fields': ['first_name', 'last_name','email','company_name'],
                'search_value': request.query_params.get('q', '') if isinstance(request.query_params.get('q', []), str) else ', '.join(request.query_params.get('q', [])),}
            return render_html_response(context, self.template_name)
        else:
            serializer = self.serializer_class(queryset, many=True)
            return create_api_response(status_code=status.HTTP_200_OK,
                                    message="Data retrieved",
                                    data=serializer.data)


class MembersListView(CustomAuthenticationMixin, generics.ListAPIView):
    """
    API view for listing members in the "Members" tab.
    This view returns a list of members, and the user can view, edit, or delete them.
    The following request methods are supported:
    - GET: Lists members.
    Note: Make sure to replace 'your_template_name.html' with the appropriate HTML template name.
    """
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'members_list.html'
    serializer_class = MemberSerializer
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
        Get the queryset based on filtering parameters from the request.
        """
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self, "survey", HasListDataPermission, 'list'
        )
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user
        filter_mapping = {
            "self": Q(user_id=self.request.user),
            "all": Q(),
        }
        base_queryset = Member.objects.filter(filter_mapping.get(data_access_value, Q())).distinct()
        # Order the queryset based on the 'ordering_fields'
        ordering = self.request.GET.get('ordering')
        if ordering in self.ordering_fields:
            base_queryset = base_queryset.order_by(ordering)

        return base_queryset.order_by('-created_at')

    @swagger_auto_schema(operation_id='Member Listing', responses={**common_get_response})
    def get(self, request, *args, **kwargs):

        """
        Handle both AJAX (JSON) and HTML requests.
        """
        
        # Call the handle_unauthenticated method to handle unauthenticated access.
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self,"survey", HasListDataPermission, 'list'
            )
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect
        filter_mapping = {
            "self": Q(user_id=self.request.user ),
            "all": Q(),  # An empty Q() object returns all data
        }


        queryset = self.get_queryset()
        if request.accepted_renderer.format == 'html':
            context = {'members':queryset, 
                     }
            return render_html_response(context,self.template_name)
        else:
            serializer = self.serializer_class(queryset, many=True)
            return create_api_response(status_code=status.HTTP_200_OK,
                                                message="Data retrieved",
                                                data=serializer.data)

class MemberFormView(generics.CreateAPIView,CustomAuthenticationMixin):
    """
    API view for creating a new member.
    This view allows users to create a new member.
    The following request methods are supported:
    - POST: Creates a new member.
    - GET: Displays a form for adding a new member.
    Note: Make sure to replace 'your_template_name.html' with the appropriate HTML template name.
    """
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'members_form.html'
    serializer_class = MemberSerializer

    @swagger_auto_schema(auto_schema=None)

    def get(self, request, *args, **kwargs):
        """
        Handle GET request to display a form for adding a new member.
        If the member exists, retrieve the serialized data and render the HTML template.
        If the member does not exist, render the HTML template with an empty serializer.
        """
        
        # Call the handle_unauthenticated method to handle unauthenticated access
        authenticated_user, data_access_value = check_authentication_and_permissions(
        self,"survey", HasCreateDataPermission, 'add'
            )

        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect

        # Filter the queryset based on the user ID
        serializer = self.serializer_class(context={'request': request})
            
        if request.accepted_renderer.format == 'html':
            context = {'serializer':serializer}
                
            return render_html_response(context,self.template_name)
        else:
            return create_api_response(status_code=status.HTTP_201_CREATED,
                                    message="GET Method Not Alloweded",)

    def post(self, request, *args, **kwargs):
        """
        Handle POST request to add a Member.
        """
      
        serializer_data = request.data 
            
        serializer = self.serializer_class(data=serializer_data, context={'request': request})
            
        message = "Member has been created successfully!"
        if serializer.is_valid():
            serializer.save()

            if request.accepted_renderer.format == 'html':
                messages.success(request, message)
                return redirect(reverse('members_list'))

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
                context = {'serializer':serializer}
                return render_html_response(context,self.template_name)
            else:   
                # Return JSON response with error message.
                return create_api_response(status_code=status.HTTP_400_BAD_REQUEST,
                                        message="We apologize for the inconvenience, but please review the below information.",
                                        data=convert_serializer_errors(serializer.errors))


class MemberEditView(generics.UpdateAPIView,CustomAuthenticationMixin):
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'members_form.html'
    serializer_class = MemberSerializer

    def get_queryset(self):
        """
        Get the queryset for listing OF MEMBERS.

        Returns:
            QuerySet: A queryset of MEMBERS filtered based on the authenticated user's ID.
        """
        # Get the model class using the provided module_name string
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self, "survey", HasUpdateDataPermission, 'change'
        )
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect

        filter_mapping = {
            "self": Q(user_id=self.request.user ),
            "all": Q(),  # An empty Q() object returns all data
        }


        queryset = Member.objects.filter(filter_mapping.get(data_access_value, Q())).distinct().order_by('-created_at')
        queryset = queryset.filter(pk=self.kwargs.get('pk')).first()
        return queryset
    
    @swagger_auto_schema(auto_schema=None)
    def get(self, request, *args, **kwargs):
        instance = self.kwargs.get('pk')
        # This method handles GET requests for updating an existing STW Requirement object.
        if request.accepted_renderer.format == 'html':
            instance = self.get_queryset()
            if instance:
                serializer = self.serializer_class(instance=instance, context={'request': request})
                context = {'serializer': serializer, 'instance': instance}
                return render_html_response(context, self.template_name)
            else:
                messages.error(request, "You are not authorized to perform this action")
                return redirect(reverse('members_list'))
    
    common_post_response = {
        status.HTTP_200_OK: 
            docs_schema_response_new(
                status_code=status.HTTP_200_OK,
                serializer_class=serializer_class,
                message = "Member has been updated successfully!",
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

    @swagger_auto_schema(operation_id='Member Edit', responses={**common_post_response})
    def post(self, request, *args, **kwargs):
        """
        Handle POST request to update a member instance.

        Args:
            request (rest_framework.request.Request): The HTTP request object.
            *args: Variable-length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            rest_framework.response.Response: HTTP response object.
                If successful, the member is updated, and the appropriate response is returned.
                If unsuccessful, an error response is returned.
        """
        instance = self.get_queryset()
        if instance:
            
            
            serializer_data = request.data 
           
            serializer = self.serializer_class(instance=instance, data=serializer_data, context={'request': request})

            if serializer.is_valid():
                # If the serializer data is valid, save the updated member instance.
                serializer.update(instance, validated_data=serializer.validated_data)
                message = "Member has been updated successfully!"

                if request.accepted_renderer.format == 'html':
                    # For HTML requests, display a success message and redirect to members_list.
                    messages.success(request, message)
                    return redirect(reverse('members_list'))
                else:
                    # For API requests, return a success response with serialized data.
                    return Response({'message': message, 'data': serializer.data}, status=status.HTTP_200_OK)
            else:
                if request.accepted_renderer.format == 'html':
                    # For HTML requests with invalid data, render the template with error messages.
                    context = {'serializer': serializer,
                     'instance': instance}
                    return render(request, self.template_name, context)
                else:
                    # For API requests with invalid data, return an error response with serializer errors.
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            error_message = "You are not authorized to perform this action"
            if request.accepted_renderer.format == 'html':
                # For HTML requests with no instance, display an error message and redirect to customer_stw_list.
                messages.error(request, error_message)
                return redirect(reverse('members_list'))
            else:
                # For API requests with no instance, return an error response with an error message.
                return Response({'message': error_message}, status=status.HTTP_400_BAD_REQUEST)



class MemberDeleteView(CustomAuthenticationMixin, generics.DestroyAPIView):

    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    serializer_class = MemberSerializer 
    template_name = 'members_form.html'


    common_delete_response = {
        status.HTTP_200_OK: 
            docs_schema_response_new(
                status_code=status.HTTP_200_OK,
                serializer_class=serializer_class,
                message = "Member has been deleted successfully!",
                ),
        status.HTTP_404_NOT_FOUND: 
            docs_schema_response_new(
                status_code=status.HTTP_404_NOT_FOUND,
                serializer_class=serializer_class,
                message = "Member not found OR You are not authorized to perform this action.",
                ),

    }
    @swagger_auto_schema(operation_id='Member Delete', responses={**common_delete_response})
    
    def delete(self, request, *args, **kwargs):
        """
        Handle DELETE request to delete a Member.
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
        queryset = Member.objects.filter(filter_mapping.get(data_access_value, Q()), pk=self.kwargs.get('pk'))
        
        member_instance = queryset.first()
        print(member_instance)

        if member_instance:
            # Proceed with the deletion
            member_instance.delete()
            messages.success(request, "Member has been deleted successfully! has been deleted successfully!")
            return create_api_response(status_code=status.HTTP_404_NOT_FOUND,
                                        message="Member has been deleted successfully! has been deleted successfully!", )
        else:
            messages.error(request, "Member not found OR You are not authorized to perform this action.")
            return create_api_response(status_code=status.HTTP_404_NOT_FOUND,
                                        message="Member not found OR You are not authorized to perform this action.", )
        
   

class MemberDetailView(CustomAuthenticationMixin,generics.RetrieveAPIView):
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'member_details.html'
    serializer_class = MemberSerializer

    def get_queryset(self):
        """
        Get the queryset for details OF MEMBERS.

        Returns:
            QuerySet: A queryset of MEMBERS filtered based on the authenticated user's ID.
        """
        # Get the model class using the provided module_name string
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self, "survey", HasUpdateDataPermission, 'view'
        )
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect

        filter_mapping = {
            "self": Q(user_id=self.request.user ),
            "all": Q(),  # An empty Q() object returns all data
        }


        queryset = Member.objects.filter(filter_mapping.get(data_access_value, Q())).distinct().order_by('-created_at')
        queryset = queryset.filter(pk=self.kwargs.get('pk')).first()
        return queryset
    
    @swagger_auto_schema(auto_schema=None)
    def get(self, request, *args, **kwargs):
        instance = self.kwargs.get('pk')
        # This method handles GET requests for updating an existing STW Requirement object.
        if request.accepted_renderer.format == 'html':
            instance = self.get_queryset()
            if instance:
                serializer = self.serializer_class(instance=instance, context={'request': request})
                context = {'serializer': serializer, 'instance': instance}
                return render_html_response(context, self.template_name)
            else:
                messages.error(request, "You are not authorized to perform this action")
                return redirect(reverse('members_list'))
    

class TeamAddView(CustomAuthenticationMixin, generics.CreateAPIView):
    serializer_class = TeamSerializer
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'team_form.html'

    @swagger_auto_schema(auto_schema=None)
    def get(self, request, *args, **kwargs):
        # Handle GET request to display a form for creating a team.
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self, "survey", HasCreateDataPermission, 'add'
        )
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user

        serializer = self.serializer_class(context={'request': request})
        members = Member.objects.all()

        if request.accepted_renderer.format == 'html':

            context = {'serializer': serializer,'members': Member.objects.all() }

            return render(request, self.template_name, context)
        else:
            return create_api_response(status_code=HTTP_201_CREATED, message="GET Method Not Allowed")

    def post(self, request, *args, **kwargs):
        data = request.data
        serializer = self.serializer_class(data=data, context={'request': request})
        message = "Team added successfully!"

        if serializer.is_valid():
            selected_member_ids = request.POST.getlist("selected_members")

            if 2 <= len(selected_member_ids) <= 6:
                # Only create the team if it has between 2 and 6 members
                team = serializer.save()

                # Fetch the selected members and associate them with the team
                associated_members = Member.objects.filter(id__in=selected_member_ids)
                team.members.set(associated_members)

                if request.accepted_renderer.format == 'html':
                    messages.success(request, message)
                    return redirect(reverse('teams_list'))
                else:
                    return create_api_response(status_code=HTTP_201_CREATED, message=message, data=serializer.data)
            else:
                error_message = "A team must have between 2 and 6 members."
                if request.accepted_renderer.format == 'html':
                    messages.error(request, error_message)
                    context = {'serializer': serializer, 'members': Member.objects.all()}
                    return render(request, self.template_name, context)
                else:
                    return create_api_response(status_code=HTTP_400_BAD_REQUEST, message=error_message)
        else:
            if request.accepted_renderer.format == 'html':
                context = {'serializer': serializer, 'members': Member.objects.all()}
                return render(request, self.template_name, context)
            else:
                return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

                
class TeamsListView(CustomAuthenticationMixin, generics.ListAPIView):
    """
    API view for listing teams in the "Teams" tab.
    This view returns a list of teams, and the user can view, edit, or delete them.
    The following request methods are supported:
    - GET: Lists teams.
    Note: Make sure to replace 'your_template_name.html' with the appropriate HTML template name.
    """
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'teams_list.html'
    serializer_class = TeamSerializer
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
        Get the queryset based on filtering parameters from the request.
        """
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self, "survey", HasListDataPermission, 'list'
        )
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user
        filter_mapping = {
            "self": Q(user_id=self.request.user),
            "all": Q(),
        }
        base_queryset = Team.objects.filter(filter_mapping.get(data_access_value, Q())).distinct()
        # Order the queryset based on the 'ordering_fields'
        ordering = self.request.GET.get('ordering')
        if ordering in self.ordering_fields:
            base_queryset = base_queryset.order_by(ordering)

        return base_queryset.order_by('-created_at')

    
    @swagger_auto_schema(operation_id='Teams Listing', responses={**common_get_response})
    def get(self, request, *args, **kwargs):

        """
        Handle both AJAX (JSON) and HTML requests.
        """
        
        # Call the handle_unauthenticated method to handle unauthenticated access.
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self,"survey", HasListDataPermission, 'list'
            )
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect

        filter_mapping = {
            "self": Q(user_id=self.request.user ),
            "all": Q(),  # An empty Q() object returns all data
        }


        queryset = self.get_queryset()
        if request.accepted_renderer.format == 'html':
            context = {'teams':queryset, 
                     }
            return render_html_response(context,self.template_name)
        else:
            serializer = self.serializer_class(queryset, many=True)
            return create_api_response(status_code=status.HTTP_200_OK,
                                                message="Data retrieved",
                                                data=serializer.data)



class TeamEditView(CustomAuthenticationMixin, generics.UpdateAPIView):

    """
    API view for editing a member.
    This view allows users to retrieve and edit member details.
    The following request methods are supported:
    - GET: Retrieves member details.
    - PUT/PATCH: Updates member details.
    Note: Make sure to replace 'your_template_name.html' with the appropriate HTML template name.
    """
    serializer_class = TeamSerializer
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'team_form.html'

    def get_queryset(self):
        """
        Get the queryset for listing Conatct items.
        Returns:
            QuerySet: A queryset of Conatct items filtered based on the authenticated user's ID.
        """

        # Get the model class using the provided module_name string
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self, "survey", HasUpdateDataPermission, 'change'
        )
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect

        # Define a mapping of data access values to corresponding filters
        filter_mapping = {
            "self": Q(user_id=self.request.user ),
            "all": Q(),  # An empty Q() object returns all data
        }

        queryset = Team.objects.filter(filter_mapping.get(data_access_value, Q()))

        # Filter the queryset based on the provided 'team_id'
        team_id = self.kwargs.get('team_id')
        instance = queryset.filter(pk=team_id).first()
        return instance

    def get(self, request, *args, **kwargs):
        instance = self.get_queryset()
        if instance:
            serializer = self.serializer_class(instance=instance, context={'request': request})

            # Fetch member data associated with the team
            members = Member.objects.filter(team=instance)

            if request.accepted_renderer.format == 'html':
                context = {
                    'serializer': serializer,
                    'team_instance': instance,
                    'members': members,  # Pass the members data to the template
                }
                return render(request, self.template_name, context)
            else:
                # Handle non-HTML formats as before
                messages.error(request, "You are not authorized to perform this action")
                return redirect(reverse('teams_list'))

    common_put_response = {
        status.HTTP_200_OK: 
            docs_schema_response_new(
                status_code=status.HTTP_200_OK,
                serializer_class=serializer_class,
                message = "Team has been updated successfully!",
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

    @swagger_auto_schema(operation_id='Edit Team', responses={**common_put_response})
    def post(self, request, *args, **kwargs):
        """
        Handle POST request to update a team instance.
        Args:
            request (rest_framework.request.Request): The HTTP request object.
            *args: Variable-length argument list.
            **kwargs: Arbitrary keyword arguments.
        Returns:
            rest_framework.response.Response: HTTP response object.
                If successful, the team is updated, and the appropriate response is returned.
                If unsuccessful, an error response is returned.
        """
        data = request.data
        instance = self.get_queryset()
        if instance:
            # If the team instance exists, initialize the serializer with instance and provided data.
            serializer = self.serializer_class(instance=instance, data=data, context={'request': request})

            message = "Team has been added successfully"
            if serializer.is_valid():
                # If the serializer data is valid, save the updated team instance.
                team = serializer.save()
                members_data = request.data.getlist('members', [])
                if 2 <= len(members_data) <= 6:
                    # Ensure there are between 2 and 6 members
                    for member_id in members_data:
                        member = Member.objects.get(id=member_id)
                        member.team = team
                        member.save()
                    if request.accepted_renderer.format == 'html':
                        messages.success(request, message)
                        return redirect(reverse('teams_list'))
                    else:
                        # Return JSON response with success message and serialized data.
                        return create_api_response(status_code=status.HTTP_201_CREATED, message=message, data=serializer.data)
                else:
                    # Team doesn't have the required number of members
                    error_message = "A team must have between 2 and 6 members."
                    if request.accepted_renderer.format == 'html':
                        messages.error(request, error_message)
                        context = {'serializer':serializer}
                        return render(request, self.template_name, context)
                    else:
                        # Return JSON response with error message
                        return create_api_response(status_code=status.HTTP_400_BAD_REQUEST, message=error_message)
        else:
            error_message = "You are not authorized to perform this action"
            if request.accepted_renderer.format == 'html':

                # For HTML requests with no instance, display an error message and redirect to vendor.

                messages.error(request, error_message)
                return redirect('teams_list')

            else:
                # For API requests with no instance, return an error response with an error message.
                return Response({'message': error_message}, status=status.HTTP_400_BAD_REQUEST)


class TeamDeleteView(CustomAuthenticationMixin, generics.DestroyAPIView):
    serializer_class = TeamSerializer
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'team_form.html'

    def delete(self, request, *args, **kwargs):
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self, "survey", HasUpdateDataPermission, 'delete'
        )

        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect

        # Define a mapping of data access values to corresponding filters
        filter_mapping = {
            "self": Q(user_id=request.user),
            "all": Q(),  # An empty Q() object returns all data
        }

        # Get the appropriate filter from the mapping based on the data access value
        queryset = Team.objects.filter(filter_mapping.get(data_access_value, Q()), pk=self.kwargs.get('pk'))

        instance = queryset.first()

        if instance:
            # Proceed with the deletion
            instance.delete()
            messages.success(request, "Your Team has been deleted successfully!")
            return create_api_response(status_code=status.HTTP_204_NO_CONTENT, message="Your Team has been deleted successfully!")
        else:
            messages.error(request, "Team not found OR You are not authorized to perform this action.")
            return create_api_response(status_code=status.HTTP_404_NOT_FOUND, message="Team not found OR You are not authorized to perform this action.")


class TeamDetailView(CustomAuthenticationMixin, generics.RetrieveAPIView):
    renderer_classes = [renderers.TemplateHTMLRenderer, renderers.JSONRenderer]
    template_name = 'team_detail.html'
    serializer_class = TeamSerializer

    def get_queryset(self):
        # Check authentication and permissions
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self, "survey", HasViewDataPermission, 'view'
        )      
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect
        filter_mapping = {
            "self": Q(user_id=self.request.user ),
            "all": Q(),  # An empty Q() object returns all data
        }
        queryset = Team.objects.filter(filter_mapping.get(data_access_value, Q())).distinct()
        queryset = queryset.filter(pk=self.kwargs.get('pk')).first()
        return queryset

    @swagger_auto_schema(auto_schema=None)
    def get(self, request, *args, **kwargs):
        if request.accepted_renderer.format == 'html':
            instance = self.get_queryset()
            if instance:
                serializer = self.serializer_class(instance=instance, context={'request': request})
                context = {
                        'serializer': serializer, 
                        'team_instance': instance, 
                    }
                return render_html_response(context, self.template_name)
        else:
            messages.error(request, "You are not authorized to perform this action")
            return redirect(reverse('teams_list', kwargs={'team_id': kwargs.get('team_id')}))



class AssignJobView(CustomAuthenticationMixin, generics.CreateAPIView):
    renderer_classes = [renderers.TemplateHTMLRenderer, renderers.JSONRenderer]
    template_name = 'assign_job/schedule_job.html'  # Replace with the actual path to your template
    serializer_class = JobAssignmentSerializer
    
    @swagger_auto_schema(auto_schema=None)
    def get(self, request, *args, **kwargs):
        """
        Handle GET request to display a form for creating a assigned job.
        Render the HTML template with an empty serializer.
        """
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self, "survey", HasCreateDataPermission, 'add'
        )
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect

        customer_id = self.kwargs.get('customer_id', None)
        customer_data = get_customer_data(customer_id)
        if not customer_data:
            messages.error(request, "You are not authorized to perform this action")
            return redirect(reverse('approved_quotation_view'))

        quotation_ids = request.query_params.get('quotation', [])
        stw_ids = request.query_params.get('stw', [])
        
        if not quotation_ids and not stw_ids:
            messages.error(request, 'No quotations was selected to create a Job, please choose a Quotation and try again.')
            return redirect(reverse('approved_quotation_list', kwargs={'customer_id': customer_data.id}))
        
        quotation_ids = [i for i in quotation_ids.split(',') if i.isdigit()] if quotation_ids else []
        stw_ids = [i for i in stw_ids.split(',') if i.isdigit()] if stw_ids else []

        if not quotation_ids and not stw_ids:
            messages.error(request, 'No quotations was selected to create a Job, please choose a Quotation and try again.')
            return redirect(reverse('approved_quotation_list', kwargs={'customer_id': customer_data.id}))

        members = Member.objects.all()
        team = Team.objects.all()
        
        requirements_dict = {'quotation':quotation_ids} if quotation_ids else {'stw':stw_ids} if stw_ids else {}

        if not requirements_dict:
            messages.error(request, 'No quotations was selected to create a Job, please choose a Quotation and try again.')
            return redirect(reverse('approved_quotation_list', kwargs={'customer_id': customer_data.id}))

        serializer = self.serializer_class(
            data={
                'start_date': timezone.now(),
                'end_date': timezone.now(),
                **requirements_dict
            },
            context={'request': request, 'customer': customer_data}
        )
        if not serializer.is_valid():
            messages.error(request, 'You are not authorised to perform this operation')
            return redirect(reverse('approved_quotation_list', kwargs={'customer_id': customer_data.id}))

        if request.accepted_renderer.format == 'html':
            context = {
                'serializer': serializer,
                'members': members,
                'teams':team,
            }
            return render(request, self.template_name, context)
        else:
            return create_api_response(status_code=status.HTTP_201_CREATED, message="GET Method Not Allowed")
        
    def post(self, request, *args, **kwargs):
        """
        Handle POST request to add or update a job.
        """
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self, "survey", HasCreateDataPermission, 'add'
        )
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect
        
        customer_id = self.kwargs.get('customer_id', None)
        customer_data = get_customer_data(customer_id)
        if not customer_data:
            messages.error(request, "You are not authorized to perform this action")
            return redirect(reverse('approved_quotation_view'))

        serializer_data = request.data
        serializer = JobCreateSerializer(data=serializer_data, context={'request': request, 'customer': customer_data})
        serializer_valid = False

        try:
            serializer_valid = serializer.is_valid()
        except AssertionError as e:
            messages.error(request, str(e))


        if serializer_valid:
            quotations = serializer.validated_data.get('quotation')
            stw = serializer.validated_data.get('stw')
            if not quotations and not stw:
                messages.error(request, 'You are not authorised to perform this operation')
                return redirect(reverse('approved_quotation_list', kwargs={'customer_id': customer_data.id}))
            
            serializer.save(customer_id=customer_data)  # Assign the created STWJob instance
            message = "Job created and assigned successfully."

            if request.accepted_renderer.format == 'html':
                messages.success(request, message)
                return redirect(reverse('jobs_list', kwargs={'customer_id': customer_data.id}))
            else:
                return create_api_response(
                    status_code=status.HTTP_201_CREATED,
                    message=message,
                    data=serializer.data
                )
        else:
            members = Member.objects.all()
            team = Team.objects.all()
            view_serializer = self.serializer_class(
                data=serializer_data,
                context={'request': request, 'customer': customer_data}
            )
            if not view_serializer.is_valid():
                messages.error(request, 'You are not authorised to perform this operation')
                return redirect(reverse('approved_quotation_list', kwargs={'customer_id': customer_data.id}))
            try:
                errors = convert_serializer_errors(serializer.errors)
                for field, error in errors.items():
                    messages.error(request, error)
            except:
                messages.error(request, 'Something went wrong while assigning job, please try again later.')
            # view_serializer._errors = serializer.errors
            # Invalid serializer data
            if request.accepted_renderer.format == 'html':
                context = {
                    'serializer': view_serializer,
                    'members': members,
                    'teams': team,
                    'selected_team': serializer.data.get('assigned_to_team', None),
                    'selected_members': serializer.data.get('assigned_to_member', None)
                }
                return render_html_response(context, self.template_name)
            else:
                return create_api_response(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    message="Please review the provided information.",
                    data=convert_serializer_errors(serializer.errors)
                )

def index(request):  
    job_id = request.GET.get('job_id')  # Retrieve job_id from query parameters
    all_events = Events.objects.all()
    context = {
        "events":all_events,
        "job_id": job_id,
    }
    return render(request,'assign_job/fullcalendar.html',context)

def all_events(request):                                                                                                 
    all_events = Events.objects.all()   
    print(all_events)                                                                                 
    out = []                                                                                                             
    for event in all_events:                                                                                             
        out.append({                                                                                                     
            'title': event.name,                                                                                         
            'id': event.id,                                                                                              
            'start': event.start.strftime("%m/%d/%Y, %H:%M:%S"),                                                         
            'end': event.end.strftime("%m/%d/%Y, %H:%M:%S"),                                                             
        })                                                                                                               
                                                                                                                      
    return JsonResponse(out, safe=False) 



def add_event(request):
    start = request.GET.get("start", None)
    end = request.GET.get("end", None)
    name = request.GET.get("title", None)
    event = Events(name=str(name), start=start, end=end)
    event.save()
    data = {}
    return JsonResponse(data)
 
# def remove(request):
#     id = request.GET.get("id", None)
#     event = Events.objects.get(id=id)
#     event.delete()
#     data = {}
#     return JsonResponse(data)



def get_event_details(request, event_id):
    try:
        event = Events.objects.get(id=event_id)
        event_data = {
            'title': event.name,
            'start': event.start,
            'end': event.end,
            'members': [member.name for member in event.members.all()],
            'team': event.team.team_name if event.team else None,
        }
        return JsonResponse(event_data)
    except Events.DoesNotExist:
        return JsonResponse({'error': 'Event not found'}, status=404)
    

# class AssignscheduleView(CustomAuthenticationMixin, generics.CreateAPIView):
#     """
#     View for adding or add job.
#     Supports both HTML and JSON response formats.
#     """
#     serializer_class = AssignJobSerializer
#     renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
#     template_name = 'assign_job/assign_schedule.html'


#     def get_queryset(self):
#         queryset = Job.objects.filter(pk=self.kwargs.get('pk')).order_by('-created_at').first()
#         return queryset

#     @swagger_auto_schema(auto_schema=None) 
#     def get(self, request, *args, **kwargs):
#         """
#         Handle GET request to display a form for updating a  job.
#         If the  job exists, retrieve the serialized data and render the HTML template.
#         If the  job does not exist, render the HTML template with an empty serializer.
#         """
#         # Call the handle_unauthenticated method to handle unauthenticated access
#         authenticated_user, data_access_value = check_authentication_and_permissions(
#            self,"survey", HasCreateDataPermission, 'add'
#         )
        
#         if isinstance(authenticated_user, HttpResponseRedirect):
#             return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect


#         if request.accepted_renderer.format == 'html':
#             context = {'serializer':self.serializer_class()}
#             return render_html_response(context,self.template_name)
#         else:
#             return create_api_response(status_code=status.HTTP_201_CREATED,
#                                 message="GET Method Not Alloweded",)
        
#     common_post_response = {
#         status.HTTP_200_OK: 
#             docs_schema_response_new(
#                 status_code=status.HTTP_200_OK,
#                 serializer_class=serializer_class,
#                 message = "Job has been assigned successfully.",
#                 ),
#         status.HTTP_400_BAD_REQUEST: 
#             docs_schema_response_new(
#                 status_code=status.HTTP_400_BAD_REQUEST,
#                 serializer_class=serializer_class,
#                 message = "We apologize for the inconvenience, but please review the below information.",
#                 ),

#     }  

#     @swagger_auto_schema(operation_id='Add Job', responses={**common_post_response})
#     def post(self, request, *args, **kwargs):
#         """
#         Handle POST request to add a job.
#         """
#         # Call the handle_unauthenticated method to handle unauthenticated access
#         authenticated_user, data_access_value = check_authentication_and_permissions(
#            self,"survey", HasCreateDataPermission, 'add'
#         )
#         message = "Job has been assigned successfully."
#         stw_job_id = self.request.query_params.get('job_id')
#         print(stw_job_id)
#         jobs_with_quotation = Job.objects.filter(quotation=int(stw_job_id)).first()
#         print(jobs_with_quotation)
#         serializer = self.serializer_class(data=request.data)
#         if serializer.is_valid():
#             # stw_job_instance = STWJob.objects.get(pk=1)
#             serializer.validated_data['stw_job'] = jobs_with_quotation
#             user = serializer.save()
#             user.save()
#             if request.accepted_renderer.format == 'html':
#                 messages.success(request, message)
#                 return redirect(reverse('job_customers_list'))

#             else:
#                 # Return JSON response with success message and serialized data
#                 return create_api_response(status_code=status.HTTP_201_CREATED,
#                                     message=message,
#                                     data=serializer.data
#                                     )
#         else:
#             # Invalid serializer data
#             if request.accepted_renderer.format == 'html':
#                 # Render the HTML template with invalid serializer data
#                 context = {'serializer':serializer}
#                 return render_html_response(context,self.template_name)
#             else:   
#                 # Return JSON response with error message
#                 return create_api_response(status_code=status.HTTP_400_BAD_REQUEST,
#                                     message="We apologize for the inconvenience, but please review the below information.",
#                                     data=convert_serializer_errors(serializer.errors))
            
class EventAddView(CustomAuthenticationMixin, generics.CreateAPIView):
    """
    View for adding or updating a event.
    Supports both HTML and JSON response formats.
    """
    serializer_class = EventSerializer
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'assign_job/event_edit.html'


    def get_queryset(self):
        """
        Get the filtered queryset for vendors based on the authenticated user.
        """
        queryset = Events.objects.filter(pk=self.kwargs.get('pk')).order_by('-created_at').first()
        return queryset

    @swagger_auto_schema(auto_schema=None) 
    def get(self, request, *args, **kwargs):
        """
        Handle GET request to display a form for updating a Event.
        If the Event exists, retrieve the serialized data and render the HTML template.
        If the Event does not exist, render the HTML template with an empty serializer.
        """
        # Call the handle_unauthenticated method to handle unauthenticated access
        authenticated_user, data_access_value = check_authentication_and_permissions(
           self,"survey", HasCreateDataPermission, 'add'
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
                message = "Event has been added successfully.",
                ),
        status.HTTP_400_BAD_REQUEST: 
            docs_schema_response_new(
                status_code=status.HTTP_400_BAD_REQUEST,
                serializer_class=serializer_class,
                message = "We apologize for the inconvenience, but please review the below information.",
                ),

    }  

    @swagger_auto_schema(operation_id='Add Event', responses={**common_post_response})
    def post(self, request, *args, **kwargs):
        """
        Handle POST request to add a Event.
        """
        # Call the handle_unauthenticated method to handle unauthenticated access
        authenticated_user, data_access_value = check_authentication_and_permissions(
           self,"survey", HasCreateDataPermission, 'add'
        )
        message = "Event has been added successfully."
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            user.save()
            if request.accepted_renderer.format == 'html':
                messages.success(request, message)
                return redirect('member_calendar')

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
class EventUpdateView(CustomAuthenticationMixin, generics.UpdateAPIView):
    """
    API view for updating a event.

    This view handles both HTML and API requests for updating a event instance.
    If the event instance exists, it will be updated with the provided data.
    Otherwise, an error message will be returned.

    The following request methods are supported:
    - POST: Updates the event instance.

    Note: Make sure to replace 'your_template_name.html' with the appropriate HTML template name.
    """
    
    serializer_class = EventSerializer
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'assign_job/event_edit.html'


    
    def get_queryset(self):
        """
        Get the queryset for listing Event items.

        Returns:
            QuerySet: A queryset of Event items filtered based on the authenticated user's ID.
        """
        
        # Get the model class using the provided module_name string
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self, "survey", HasUpdateDataPermission, 'change'
        )
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect

        # Define a mapping of data access values to corresponding filters
        filter_mapping = {
            "self": Q(user_id=self.request.user ),
            "all": Q(),  # An empty Q() object returns all data
        }

        queryset = Events.objects.filter(filter_mapping.get(data_access_value, Q()))

        # Filter the queryset based on the provided 'event_id'
        event_id = self.kwargs.get('event_id')
        instance = queryset.filter(pk=event_id).first()
        return instance
    
    def update_members_and_team(self, event, members, team):
        event.members.clear()
        event.members.add(*members)
        event.team = team
        event.save()

    @swagger_auto_schema(auto_schema=None) 
    def get(self, request, *args, **kwargs):
        event_id = self.kwargs.get('event_id')
        # This method handles GET requests for updating an existing event object.
        if request.accepted_renderer.format == 'html':
            instance = self.get_queryset()
            print(instance)
            if instance:
                serializer = self.serializer_class(instance=instance, context={'request': request})
                context = {'serializer': serializer, 'event_instance': instance,'event_id':event_id}
                return render_html_response(context, self.template_name)
            else:
                messages.error(request, "You are not authorized to perform this action")
                return redirect(reverse('member_calendar'))
            
    common_put_response = {
        status.HTTP_200_OK: 
            docs_schema_response_new(
                status_code=status.HTTP_200_OK,
                serializer_class=serializer_class,
                message = "Event has been updated successfully!",
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

    @swagger_auto_schema(operation_id='Edit Event', responses={**common_put_response})
    def post(self, request, *args, **kwargs):
        """
        Handle POST request to update a Event instance.

        Args:
            request (rest_framework.request.Request): The HTTP request object.
            *args: Variable-length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            rest_framework.response.Response: HTTP response object.
                If successful, the Event is updated, and the appropriate response is returned.
                If unsuccessful, an error response is returned.
        """
        event_id = self.kwargs.get('event_id')
        data = request.data.copy()
        instance = self.get_queryset()
        if instance:
            # If the Event instance exists, initialize the serializer with instance and provided data.
            serializer = self.serializer_class(instance=instance, data=data, context={'request': request})

            if serializer.is_valid():
                # If the serializer data is valid, save the updated Event instance.
                members = request.data.getlist('member', [])
                serializer.save()

                
                team_id = serializer.validated_data.get('team', None)   

                try:
                    team_id = int(team_id)
                except (TypeError, ValueError):
                    team_id = None

                team_instance = Team.objects.filter(id=team_id).first()

                if team_instance:
                    self.update_members_and_team(instance, members, team_instance)
                message = "Event has been updated successfully!"

                if request.accepted_renderer.format == 'html':

                    # For HTML requests, display a success message and redirect to Event.

                    messages.success(request, message)
                    return redirect('member_calendar')
                else:
                    # For API requests, return a success response with serialized data.
                    return Response({'message': message, 'data': serializer.data}, status=status.HTTP_200_OK)
            else:
                if request.accepted_renderer.format == 'html':
                    # For HTML requests with invalid data, render the template with error messages.
                    context = {'serializer': serializer, 'event_instance': instance}
                    return render(request, self.template_name, context)
                else:
                    # For API requests with invalid data, return an error response with serializer errors.
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            error_message = "You are not authorized to perform this action"
            if request.accepted_renderer.format == 'html':

                # For HTML requests with no instance, display an error message and redirect to event.

                messages.error(request, error_message)
                return redirect('assign_job/event_edit')

            else:
                # For API requests with no instance, return an error response with an error message.
                return Response({'message': error_message}, status=status.HTTP_400_BAD_REQUEST)
        
class EventdetailView(CustomAuthenticationMixin, generics.RetrieveAPIView):
    """
    View for retrieving event.

    This view retrieves details of a job, optionally filtered and searchable.
    It provides both HTML and JSON rendering.

    Attributes:
        serializer_class (JobSerializer): The serializer class for the event.
        renderer_classes (list): The renderer classes for HTML and JSON.
        template_name (str): The template name for HTML rendering.
    """

    serializer_class = JobListSerializer
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'assign_job/event_view.html'

    def get_queryset(self):
        """
        Get the queryset of event.

        Returns:
        QuerySet: A queryset of event.
        """
        # Your queryset logic to filter jobs goes here
        queryset = Events.objects.all()
        return queryset

    def get(self, request, *args, **kwargs):
        event_id = self.kwargs.get('event_id')
        queryset = self.get_queryset()

        try:
            event = queryset.get(id=event_id)
        except Events.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        # Additional job data can be retrieved here based on your requirements

        if request.accepted_renderer.format == 'html':
            context = {
                'event': event,
                # Add more job-related data to the context as needed
            }
            return render(request, self.template_name, context)
        else:
            serializer = self.serializer_class(event)
            return create_api_response(status_code=status.HTTP_200_OK,
                                    message="Data retrieved",
                                    data=serializer.data)

def retriveMembersAssignedJobs(request):
    if request.method == "GET":
        teamId = request.GET.get('team', None)
        membersIds = request.GET.get('members', None)
        
        if not teamId and not membersIds:
            return create_api_response(
                status_code=status.HTTP_200_OK,
                message="Assigned Jobs",
                data=[]
            )

        team = Team.objects.filter(id__in=[i for i in teamId.split(',') if i.isdigit()]).all() if teamId else None
        members = Member.objects.filter(id__in=[i for i in membersIds.split(',') if i.isdigit()]).all() if membersIds else None
        
        if not team and not members:
            return create_api_response(
                status_code=status.HTTP_200_OK,
                message="Assigned Jobs",
                data=[]
            )
        
        serializer = MemberCalendarSerializer([member for t in team for member in t.members.all()] if team else members)
        return create_api_response(
            status_code=status.HTTP_200_OK,
            message="Assigned Jobs",
            data=serializer.data.get('jobs')
        )

    return JsonResponse({"error": "Invalid request"}, status=400)
