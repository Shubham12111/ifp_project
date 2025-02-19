from infinity_fire_solutions.aws_helper import *
from infinity_fire_solutions.permission import *
from infinity_fire_solutions.response_schemas import create_api_response, render_html_response
from rest_framework import generics, status
from rest_framework.renderers import TemplateHTMLRenderer, JSONRenderer
from .quotation_serializers import *
from rest_framework import filters
from infinity_fire_solutions.email import *
from .views import get_customer_data
from .models import Requirement, Report, SORItem,Quotation, QUOTATION_STATUS_CHOICES
from django.contrib import messages
from django.db.models import F
from django.http import JsonResponse
from infinity_fire_solutions.custom_form_validation import *
from datetime import datetime
from infinity_fire_solutions.email import *
import uuid
from work_planning_management.models import Job
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from requirement_management.serializers import RequirementReportListSerializer, RequirementQuotationListSerializer


class QuotationCustomerListView(CustomAuthenticationMixin,generics.ListAPIView):
    serializer_class = QuotationCustomerSerializer
    renderer_classes = [TemplateHTMLRenderer,JSONRenderer]
    filter_backends = [filters.SearchFilter]
    search_fields = ['company_name']
    template_name = 'quote/quotation_customer_list.html'
    ordering_fields = ['created_at'] 

    def get_queryset(self):
        reports = Report.objects.filter(
            status__in=['submit'],
        ).order_by('requirement_id__customer_id').values_list('requirement_id__customer_id', flat=True).distinct()
        
        if not reports:
            return []
        
        queryset = User.objects.filter(
            is_active=False,  roles__name__icontains='customer',
            id__in=reports
            ).exclude(pk=self.request.user.id)
        return queryset
    
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
        paginator = Paginator(self.get_searched_queryset(base_queryset), items_per_page)
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

    def get(self, request, *args, **kwargs):
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self, "fire_risk_assessment", HasListDataPermission, 'list'
        )
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect

        if request.user.roles.name == 'customer_contact':
            contact_person = request.user.contactperson
            customer_meta = contact_person.customer if contact_person else None
            customer = customer_meta.user_id if customer_meta else None
            if not customer:
                messages.error(request, "You are not authorized to perform this action")
                return redirect(reverse('dashboard'))        
            return redirect(reverse('view_customer_fra_list_report', kwargs={'customer_id': customer.id}))

        queryset = self.get_queryset()    
        reports = Report.objects.filter()

        
        customers_with_counts = []  # Create a list to store customer objects with counts

        for customer in queryset:
            report_counts = reports.filter(requirement_id__customer_id=customer, status__in=['submit'], quotations__isnull=True).count()
            # Check if the user has any roles before accessing the first one
            
            customers_with_counts.append({
                'customer': customer,
                'report_counts': report_counts
            })
        

        if request.accepted_renderer.format == 'html':
            context = {'queryset': self.get_paginated_queryset(customers_with_counts),
                       'search_fields': self.search_fields,
                        'search_value': request.query_params.get('q', '') if isinstance(request.query_params.get('q', []), str) else ', '.join(request.query_params.get('q', [])),
                }  # Pass the list of customers with counts to the template
            return render_html_response(context, self.template_name)
        else:
            serializer = self.serializer_class(queryset, many=True)
            return create_api_response(status_code=status.HTTP_200_OK,
                                    message="Data retrieved",
                                    data=serializer.data)

class QuotationCustomerReportListView(CustomAuthenticationMixin,generics.ListAPIView):
    
    serializer_class = RequirementReportListSerializer
    renderer_classes = [TemplateHTMLRenderer,JSONRenderer]
    filter_backends = [filters.SearchFilter]
    search_fields = ['requirement_id__action', 'requirement_id__description', 'requirement_id__UPRN']
    template_name = 'quote/quotation_customer_report_list.html'
    ordering_fields = ['created_at'] 

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

    def get_filtered_queryset(self, queryset):
        # Get the filtering parameters from the request's query parameters
        filters = {
            'surveyor': self.request.GET.get('surveyor'),
        }

        # Apply additional filters based on the received parameters
        for filter_name, filter_value in filters.items():
            if filter_value:
                value_list = filter_value.split()
                if 2 >= len(value_list) > 1:
                    queryset = queryset.filter(requirement_id__surveyor__first_name=value_list[0], requirement_id__surveyor__last_name=value_list[1])
                else:
                    queryset = queryset.filter(requirement_id__surveyor__first_name = filter_value)
                    
        
        return self.get_searched_queryset(queryset)

    def get_queryset(self):

        queryset = Report.objects.filter(
            requirement_id__customer_id=self.kwargs.get('customer_id'), 
            status = 'submit',
            quotations__isnull=True
        )
        return self.get_filtered_queryset(queryset)

    def get(self, request, *args, **kwargs):
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self, "fire_risk_assessment", HasListDataPermission, 'list'
        )
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect

        customer_id = kwargs.get('customer_id')
        customer_data = get_customer_data(customer_id)

        if customer_data:
            queryset = self.get_queryset()
            report_list = self.serializer_class(queryset, many=True).data
            if request.accepted_renderer.format == 'html':
                context = {'report_list': self.get_paginated_queryset(report_list),
                'customer_id': customer_id,
                'customer_data':customer_data,
                'search_fields': self.search_fields,
                'search_value': request.query_params.get('q', '') if isinstance(request.query_params.get('q', []), str) else ', '.join(request.query_params.get('q', []))}  # Pass the list of customers with counts to the template
                return render_html_response(context, self.template_name)
            else:
                serializer = self.serializer_class(queryset, many=True)
                return create_api_response(status_code=status.HTTP_200_OK,
                                        message="Data retrieved",
                                        data=serializer.data)
        else:
            messages.error(request, "You are not authorized to perform this action")
            return redirect(reverse('view_customer_list_quotation'))


from django.forms import modelformset_factory
from customer_management.models import *
from django.core import serializers
import json 
from decimal import Decimal



# Custom JSON encoder that can handle Decimal instances
class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)  # Convert Decimal to a string
        return super(DecimalEncoder, self).default(obj)



class QuotationAddView(CustomAuthenticationMixin,generics.ListAPIView):
    
    renderer_classes = [TemplateHTMLRenderer,JSONRenderer]
    filter_backends = [filters.SearchFilter]
    search_fields = ['customer_id__first_name', 'customer_id__last_name']
    template_name = 'quote/quotation_create.html'
    ordering_fields = ['created_at'] 
    
    def get_queryset(self):
        """
        Get the filtered queryset for requirements based on the authenticated user.
        """
        queryset = Report.objects.filter(id=self.kwargs.get('report_id')).first()
        
        return queryset

    def get_quotation_data(self, quotation_id=None):
        """
        Retrieve quotation-related data.

        Args:
            self: The instance of the calling class.
            quotation_id (int, optional): The ID of the quotation to retrieve. Defaults to None.

        Returns:
            tuple: A tuple containing the following items:
                - quotation_data (Quotation or dict): The Quotation instance if found, or an empty dictionary.
                - report_instance (Report): The associated Report instance.
                - requirement_instance (Requirement): The associated Requirement instance.
                - requiremnt_defect_instances (QuerySet): QuerySet of associated Defect instances.
        """
        if quotation_id:
            # Retrieve the Quotation instance if a quotation_id is provided
            quotation_data = Quotation.objects.filter(id=quotation_id, status='draft').first()
        else:
            # If no quotation_id is provided, set quotation_data as an empty dictionary
            quotation_data = {}

        # Determine the report_instance based on quotation_data or the queryset
        report_instance = quotation_data.report_id if quotation_data else self.get_queryset()

        if not report_instance:
            # If report_instance is not found, set it to None
            report_instance = None

        # Retrieve the associated Requirement instance
        requirement_instance = report_instance.requirement_id if report_instance else None

        if quotation_data:
            requiremnt_defect_instances = quotation_data.defect_id.all()
        else:
            # Retrieve all associated Defect instances
            requiremnt_defect_instances = report_instance.defect_id.all() if report_instance else []

        return quotation_data, report_instance, requirement_instance, requiremnt_defect_instances



    def get(self, request, *args, **kwargs):
        authenticated_user, data_access_value = check_authentication_and_permissions(
           self,"fire_risk_assessment", HasCreateDataPermission, 'detail'
        )
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect

        customer_id = kwargs.get('customer_id')
        customer_data = get_customer_data(customer_id)
        report_instance = {}
        if customer_data:
            customer_address = BillingAddress.objects.filter(user_id=customer_data).first()
            report_id = kwargs.get('pk')
            # This method handles GET requests for updating an existing Requirement object.
            if request.accepted_renderer.format == 'html':

                quotation_id = self.kwargs.get('quotation_id')
                quotation_data, report_instance, requirement_instance, requiremnt_defect_instances = self.get_quotation_data(quotation_id)
                all_sors = SORItem.objects.filter(customer_id=customer_data).values('id','name','reference_number', 'category_id__name', 'price',)

                if not all_sors:
                    all_sors = SORItem.objects.filter(customer_id__isnull=True).values('id','name','reference_number', 'category_id__name', 'price',)

                # Convert the queryset of dictionaries to a list
                all_sors_list = list(all_sors)

                # Serialize the list to JSON
                all_sors_json = json.dumps(all_sors_list, cls=DecimalEncoder)

                if report_instance or quotation_data:

                    context = {
                        'requirement_instance': requirement_instance,  
                        'report_instance':report_instance,
                        'requiremnt_defect_instances': requiremnt_defect_instances,
                        'customer_id': kwargs.get('customer_id'),
                        'customer_data':customer_data,
                        'all_sors': all_sors_json,
                        'customer_address':customer_address,
                        'quotation_data':quotation_data
                        }
            

                    return render_html_response(context, self.template_name)
                else:
                    messages.error(request, "You are not authorized to perform this action")
                    return redirect(reverse('view_customer_quotation_list', kwargs={'customer_id': kwargs.get('customer_id')}))
        else:
            messages.error(request, "You are not authorized to perform this action")
            return redirect(reverse('view_customer_quotation_list', kwargs={'customer_id': kwargs.get('customer_id')}))
    
 
    def post(self, request, *args, **kwargs):
        customer_id = kwargs.get('customer_id')
        customer_data = get_customer_data(customer_id)
        quotation_data = {}
        defectList = []
        message = f"Your quotation has been added successfully!"
        
        if customer_data:
            quotation_id = self.kwargs.get('quotation_id')
            quotation_data, report_instance, requirement_instance, requiremnt_defect_instances = self.get_quotation_data(quotation_id)
            customer_address =  BillingAddress.objects.filter(user_id=customer_data).first()

            data = request.data

            if request.data.get('defectList'):
                defectList = request.data.get('defectList')
            
            sor_id_list = []  # Initialize a list to store 'sor-id' values
            sor_items_dict = {}  # Initialize a dictionary to store SORItem data

            if 'defectSorValues' in data:
                defect_sor_values = data['defectSorValues']

                # Extract 'sor-id' values from the JSON data and initialize corresponding lists
                for key in defect_sor_values:
                    sor_items_dict[key] = {}

                    for sub_key in defect_sor_values[key]:
                        sor_id = defect_sor_values[key][sub_key].get('sor-id')
                        if sor_id:
                            sor_id_list.append(sor_id)

                # Fetch SORItem objects based on 'sor-id'
                sor_items = SORItem.objects.filter(id__in=sor_id_list)

                # Convert SORItem objects to dictionaries
                sor_items_data = {item.id: item.to_dict() for item in sor_items}

                # Populate the 'sor_items' data under each 'sor-id' key
                for key in defect_sor_values:
                    for sub_key in defect_sor_values[key]:
                        sor_id = defect_sor_values[key][sub_key].get('sor-id')
                        if sor_id:
                            sor_items_dict[key][sub_key] = {
                                'sor-id': sor_id,
                                'price': float(defect_sor_values[key][sub_key].get('price')),
                                'total_price': float(defect_sor_values[key][sub_key].get('price')) * int(defect_sor_values[key][sub_key].get('quantity', 1)),
                                'quantity': int(defect_sor_values[key][sub_key].get('quantity', 1)),
                                'sor_items': sor_items_data.get(int(sor_id), [])  # Reference 'sor_items_data' using the 'sor-id'
                            }
            # Create a dictionary to store the final JSON data
            json_data = {
                'status': 'draft',
                'defectSorValues': sor_items_dict,
                'defectList': defectList,
            }
            # The 'json_data' dictionary now contains the desired structure.

            if not quotation_data:
                # Assuming you have a Quotation instance (replace `quotation_instance` with your instance)
                quotation_instance = Quotation.objects.create(
                    user_id=request.user,  # Replace with the actual user instance
                    customer_id=customer_data,  # Replace with the actual customer user instance
                    requirement_id=requirement_instance,  # Replace with the actual Requirement instance
                    report_id=report_instance,  # Replace with the actual Report instance
                    status=request.data.get('status'),  # Replace with the desired status
                    total_amount=request.data.get('total_amount'), 
                    quotation_json=json_data  # Use the constructed JSON data
                )
                
            else:
                quotation_instance = quotation_data
                # Update the Quotation instance with the values from `updated_quotation_data`
                quotation_instance.status = request.data.get('status')
                quotation_instance.total_amount = request.data.get('total_amount')
                # If you want to update the `quotation_json` field, update it accordingly
                quotation_instance.quotation_json = json_data

                # Save the updated Quotation instance
                quotation_instance.save()

            if defectList:
                quotation_instance.defect_id.set(defectList) 



            if request.data.get('status') == "quoted":
                quotation_instance.submitted_at = datetime.now() 
                unique_pdf_filename = f"{str(uuid.uuid4())}_quotation_{requirement_instance.id}.pdf"
                context= {
                    'customer_id': customer_id,
                    'customer_data':customer_data,
                    'customer_address':customer_address,
                    'requirement_instance':requirement_instance,
                    'queryset':quotation_instance
                }
                pdf_file = save_pdf_from_html(context=context, file_name=unique_pdf_filename, content_html = 'quote/quotation_pdf.html')
                pdf_path = f'requirement/{requirement_instance.id}/quotation/pdf'
                
                upload_signature_to_s3(unique_pdf_filename, pdf_file, pdf_path)
                
                quotation_instance.pdf_path = f'requirement/{requirement_instance.id}/quotation/pdf/{unique_pdf_filename}'
                quotation_instance.save()

            messages.success(request, message)
            return JsonResponse({'success': True,  'status':status.HTTP_204_NO_CONTENT})  # Return success response

class QuotationSendForApprovalView(CustomAuthenticationMixin, generics.GenericAPIView):
    """
    View for sending a quotation for approval to a customer.
    """
    
    renderer_classes = [TemplateHTMLRenderer,JSONRenderer]
    queryset = Quotation.objects.filter(status='quoted').all()  # Queryset of quoted quotations

    def get_queryset(self, customer):
        """
        Retrieves the quotation queryset filtered by customer and quotation ID.

        Arguments:
            self: The instance of the class.
            customer: The customer object.

        Returns:
            Quotation: The quotation instance.
        """
        queryset = super().get_queryset()
        pk = self.kwargs.get('quotation_id', None)

        if queryset and customer and pk:
            instance = queryset.filter(customer_id=customer, pk=pk).first()
            return instance

        return None
    
    def get(self, request, *args, **kwargs):
        """
        Handles GET request to send a quotation for approval to a customer.

        Arguments:
            self: The instance of the class.
            request: The HTTP request object.
            args: Additional arguments passed to the view.
            kwargs: Additional keyword arguments passed to the view.

        Returns:
            HttpResponseRedirect: Redirects the user to a specific URL after sending the quotation for approval.
        """
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self, "fire_risk_assessment", HasUpdateDataPermission, 'change'
        )
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect
        
        customer_id = kwargs.get('customer_id')
        customer = get_customer_data(customer_id)

        if not customer:
            messages.error(request, 'You are not authorized to perform this task.')
            return redirect(reverse('view_customer_list_quotation'))
        
        instance = self.get_queryset(customer)
        if not instance:
            messages.error(request, 'You are not authorized to perform this task.')
            return redirect(reverse('view_customer_quotation_list', kwargs={'customer_id': customer.id}))
        
        customermeta = customer.customermeta
        if not customermeta:
            messages.error(request, 'You are not authorized to perform this task.')
            return redirect(reverse('view_customer_quotation_list', kwargs={'customer_id': customer.id}))
        
        if not customermeta.email:
            messages.error(request, 'No Customer email found, please add a email in Customer General Information.')
            return redirect(reverse('view_customer_quotation_list', kwargs={'customer_id': customer.id}))

        context = {
            'user': customer,
        }

        email = Email()
        attachment_path = generate_presigned_url(instance.pdf_path)

        try:
            email.send_mail(
                customermeta.email, 
                'email_templates/quotation_client.html', 
                context, 
                "Quotation Submission for Review", 
                attachment_path
            )
        except Exception as e:
            pass

        instance.status = 'awaiting-approval'
        instance.save()

        messages.success(request, 'Your Quotation has been sent to the customer for review successfully!')
        return redirect(reverse('view_customer_quotation_list', kwargs={'customer_id': customer.id}))

class QuotationApproveView(CustomAuthenticationMixin, generics.GenericAPIView):
    """
    View for approving a quotation.
    """
    
    renderer_classes = [TemplateHTMLRenderer,JSONRenderer]
    queryset = Quotation.objects.filter(status='awaiting-approval').all()  # Queryset of awaiting-approval quotations

    def get_queryset(self, customer):
        """
        Retrieves the quotation queryset filtered by customer and quotation ID.

        Arguments:
            self: The instance of the class.
            customer: The customer object.

        Returns:
            Quotation: The quotation instance.
        """
        queryset = super().get_queryset()
        pk = self.kwargs.get('quotation_id', None)

        if queryset and customer and pk:
            instance = queryset.filter(customer_id=customer, pk=pk).first()
            return instance

        return None
    
    def get(self, request, *args, **kwargs):
        """
        Handles GET request to approve a quotation.

        Arguments:
            self: The instance of the class.
            request: The HTTP request object.
            args: Additional arguments passed to the view.
            kwargs: Additional keyword arguments passed to the view.

        Returns:
            HttpResponseRedirect: Redirects the user to a specific URL after approving the quotation.
        """
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self, "fire_risk_assessment", HasUpdateDataPermission, 'change'
        )
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect
        
        customer_id = kwargs.get('customer_id')
        customer = get_customer_data(customer_id)

        if not customer:
            messages.error(request, 'You are not authorized to perform this task.')
            return redirect(reverse('view_customer_list_quotation'))
        
        instance = self.get_queryset(customer)
        if not instance:
            messages.error(request, 'You are not authorized to perform this task.')
            return redirect(reverse('view_customer_quotation_list', kwargs={'customer_id': customer.id}))
        

        instance.status = 'to-commence'
        instance.save()

        messages.success(request, 'Your Quotation has been approved successfully!')
        return redirect(reverse('view_customer_quotation_list', kwargs={'customer_id': customer.id}))


class CustomerQuotationListView(CustomAuthenticationMixin,generics.ListAPIView):
    
    renderer_classes = [TemplateHTMLRenderer,JSONRenderer]
    filter_backends = [filters.SearchFilter]
    search_fields = ['requirement_id__action', 'requirement_id__description', 'requirement_id__UPRN']
    template_name = 'quote/customer_quotation_list.html'
    ordering_fields = ['created_at'] 
    serializer_class = RequirementQuotationListSerializer

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

    def get_filtered_queryset(self, queryset):
        # Get the filtering parameters from the request's query parameters
        filters = {
            'surveyor': self.request.GET.get('surveyor'),
            'status': self.request.GET.get('status'),
        }

        # Apply additional filters based on the received parameters
        for filter_name, filter_value in filters.items():
            if filter_value:
                if filter_name == 'surveyor':
                    value_list = filter_value.split()
                    if 2 >= len(value_list) > 1:
                        queryset = queryset.filter(requirement_id__surveyor__first_name=value_list[0], requirement_id__surveyor__last_name=value_list[1])
                    else:
                        queryset = queryset.filter(requirement_id__surveyor__first_name = filter_value)
                else:
                    # For other filters, apply the corresponding filters on the queryset
                    filter_mapping = {
                        'status': 'status',
                    }
                    queryset = queryset.filter(**{filter_mapping[filter_name]: filter_value.strip()})
                    
        
        return self.get_searched_queryset(queryset)

    def get_queryset(self):
        queryset = Quotation.objects.filter(requirement_id__customer_id=self.kwargs.get('customer_id'), status__in=['draft', 'quoted', 'awaiting-approval', 'rejected'])
        return self.get_filtered_queryset(queryset)

    def get(self, request, *args, **kwargs):
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self, "fire_risk_assessment", HasListDataPermission, 'list'
        )
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect

        customer_id = kwargs.get('customer_id')
        customer_data = get_customer_data(customer_id)

        if customer_data:
            queryset = self.get_queryset()
            quotation_list = self.serializer_class(queryset, many=True).data
            if request.accepted_renderer.format == 'html':
                context = {'quotation_list': self.get_paginated_queryset(quotation_list),
                'customer_id': customer_id,
                'customer_data':customer_data,
                'status_values': QUOTATION_STATUS_CHOICES,
                'search_fields': self.search_fields,
                'search_value': request.query_params.get('q', '') if isinstance(request.query_params.get('q', []), str) else ', '.join(request.query_params.get('q', []))}  # Pass the list of customers with counts to the template
                return render_html_response(context, self.template_name)
        else:
            messages.error(request, "You are not authorized to perform this action")
            return redirect(reverse('view_customer_list_quotation'))



class CustomerQuotationView(CustomAuthenticationMixin,generics.ListAPIView):
    
    renderer_classes = [TemplateHTMLRenderer,JSONRenderer]
    filter_backends = [filters.SearchFilter]
    template_name = 'quote/quotation_view.html'


    def get_queryset(self):
        queryset = Quotation.objects.filter(requirement_id__customer_id=self.kwargs.get('customer_id'),
        pk= self.kwargs.get('quotation_id')).first()
        return queryset

    def get(self, request, *args, **kwargs):
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self, "fire_risk_assessment", HasListDataPermission, 'list'
        )
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect

        customer_id = kwargs.get('customer_id')
        customer_data = get_customer_data(customer_id)

        if customer_data:
            customer_address = BillingAddress.objects.filter(user_id=customer_data).first()
            queryset = self.get_queryset()
            requirement_instance = queryset.requirement_id

            

            if request.accepted_renderer.format == 'html':
                context = {
                    'quotation_list': queryset,
                    'customer_id': customer_id,
                    'customer_data':customer_data,
                    'customer_address':customer_address,
                    'requirement_instance':requirement_instance,
                    'queryset':queryset
                    }  # Pass the list of customers with counts to the template
                return render_html_response(context, self.template_name)
        else:
            messages.error(request, "You are not authorized to perform this action")
            return redirect(reverse('view_customer_list_quotation'))