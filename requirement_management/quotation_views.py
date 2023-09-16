from infinity_fire_solutions.aws_helper import *
from infinity_fire_solutions.permission import *
from infinity_fire_solutions.response_schemas import create_api_response, render_html_response
from rest_framework import generics, status
from rest_framework.renderers import TemplateHTMLRenderer, JSONRenderer
from .quotation_serializers import *
from rest_framework import filters
from infinity_fire_solutions.email import *
from .views import get_customer_data
from .models import Requirement, Report, SORItem,Quotation
from django.contrib import messages
from django.db.models import F
from django.http import JsonResponse
from infinity_fire_solutions.custom_form_validation import *
import uuid


class QuotationCustomerListView(CustomAuthenticationMixin,generics.ListAPIView):
    
    serializer_class = CustomerSerializer
    renderer_classes = [TemplateHTMLRenderer,JSONRenderer]
    filter_backends = [filters.SearchFilter]
    search_fields = ['customer_id__first_name', 'customer_id__last_name']
    template_name = 'quote/quotation_customer_list.html'
    ordering_fields = ['created_at'] 

    def get_queryset(self):
            queryset = User.objects.filter(is_active=True,  roles__name__icontains='customer').exclude(pk=self.request.user.id)
            return queryset

    def get(self, request, *args, **kwargs):
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self, "fire_risk_assessment", HasListDataPermission, 'list'
        )
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect

        queryset = self.get_queryset()    
        

        if request.accepted_renderer.format == 'html':
            context = {'queryset': queryset}  # Pass the list of customers with counts to the template
            return render_html_response(context, self.template_name)
        else:
            serializer = self.serializer_class(queryset, many=True)
            return create_api_response(status_code=status.HTTP_200_OK,
                                    message="Data retrieved",
                                    data=serializer.data)

class QuotationCustomerReportListView(CustomAuthenticationMixin,generics.ListAPIView):
    
    serializer_class = CustomerSerializer
    renderer_classes = [TemplateHTMLRenderer,JSONRenderer]
    filter_backends = [filters.SearchFilter]
    search_fields = ['customer_id__first_name', 'customer_id__last_name']
    template_name = 'quote/quotation_customer_report_list.html'
    ordering_fields = ['created_at'] 

    def get_queryset(self):

            queryset = Report.objects.filter(requirement_id__customer_id=self.kwargs.get('customer_id'), 
            status = 'submit')
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
            queryset = self.get_queryset()
            if request.accepted_renderer.format == 'html':
                context = {'report_list': queryset,
                'customer_id': customer_id,
                'customer_data':customer_data}  # Pass the list of customers with counts to the template
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
        authenticated_user, data_access_value = check_authentication_and_permissions(
           self,"fire_risk_assessment", HasCreateDataPermission, 'detail'
        )
        
        queryset = Report.objects.filter(id=self.kwargs.get('report_id')).get()
        
        return queryset


    def get(self, request, *args, **kwargs):
        customer_id = kwargs.get('customer_id')
        customer_data = get_customer_data(customer_id)
        if customer_data:
            customer_address = BillingAddress.objects.filter(user_id=customer_data).first()
            report_id = kwargs.get('pk')
            # This method handles GET requests for updating an existing Requirement object.
            if request.accepted_renderer.format == 'html':
                report_instance = self.get_queryset()
                
                requirement_instance = report_instance.requirement_id
                requiremnt_defect_instances = report_instance.defect_id.all()

                all_sors = SORItem.objects.filter(customer_id=customer_data).values('id','name','reference_number', 'category_id__name', 'price',)

                # Convert the queryset of dictionaries to a list
                all_sors_list = list(all_sors)

                # Serialize the list to JSON
                all_sors_json = json.dumps(all_sors_list, cls=DecimalEncoder)
                if report_instance:

                    context = {
                        'requirement_instance': requirement_instance,  
                        'report_instance':report_instance,
                        'requiremnt_defect_instances': requiremnt_defect_instances,
                        'customer_id': kwargs.get('customer_id'),
                        'customer_data':customer_data,
                        'all_sors': all_sors_json,
                        'customer_address':customer_address
                        }
            

                    return render_html_response(context, self.template_name)
                else:
                    messages.error(request, "You are not authorized to perform this action")
                    return redirect(reverse('view_customer_list_quotation', kwargs={'customer_id': kwargs.get('customer_id')}))
        else:
            messages.error(request, "You are not authorized to perform this action")
            return redirect(reverse('view_customer_list_quotation', kwargs={'customer_id': kwargs.get('customer_id')}))
    
 
    def post(self, request, *args, **kwargs):
        customer_id = kwargs.get('customer_id')
        customer_data = get_customer_data(customer_id)
        if customer_data:
            report_instance = self.get_queryset()
            data = request.data

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
                sor_items_data = [item.to_dict() for item in sor_items]

                # Populate the 'sor_items' data under each 'sor-id' key
                for key in defect_sor_values:
                    for sub_key in defect_sor_values[key]:
                        sor_id = defect_sor_values[key][sub_key].get('sor-id')
                        if sor_id:
                            sor_items_dict[key][sub_key] = {
                                'sor-id': sor_id,
                                'price': defect_sor_values[key][sub_key].get('price'),
                                'sor_items': sor_items_data
                            }

            # Create a dictionary to store the final JSON data
            json_data = {
                'status': 'draft',
                'defectSorValues': sor_items_dict,
            }
            
            # Assuming you have a Quotation instance (replace `quotation_instance` with your instance)
            quotation_instance = Quotation.objects.create(
                user_id=request.user,  # Replace with the actual user instance
                customer_id=customer_data,  # Replace with the actual customer user instance
                requirement_id=report_instance.requirement_id,  # Replace with the actual Requirement instance
                report_id=report_instance,  # Replace with the actual Report instance
                status=request.data.get('status'),  # Replace with the desired status
                quotation_json=json_data  # Use the constructed JSON data
            )

            if request.data.get('status') == "submitted":
                unique_pdf_filename = f"{str(uuid.uuid4())}_quotation_{report_instance.requirement_id.id}.pdf"
                context= {'quotation_instance':quotation_instance,
                            'customer_data':customer_data
                        }
                pdf_file = save_pdf_from_html(context=context, file_name=unique_pdf_filename, content_html = 'quote/quotation_pdf.html')
                pdf_path = f'requirement/{report_instance.requirement_id.id}/quotation/pdf'
                
                upload_signature_to_s3(unique_pdf_filename, pdf_file, pdf_path)
                
                quotation_instance.pdf_path = f'requirement/{report_instance.requirement_id.id}/quotation/pdf/{unique_pdf_filename}'
                quotation_instance.save()

            message = f"Your quotation has been added successfully!"
            messages.success(request, message)
            return JsonResponse({'success': True,  'status':status.HTTP_204_NO_CONTENT})  # Return success response


class CustomerQuotationListView(CustomAuthenticationMixin,generics.ListAPIView):
    
    renderer_classes = [TemplateHTMLRenderer,JSONRenderer]
    filter_backends = [filters.SearchFilter]
    search_fields = ['customer_id__first_name', 'customer_id__last_name']
    template_name = 'quote/customer_quotation_list.html'
    ordering_fields = ['created_at'] 

    def get_queryset(self):
        queryset = Quotation.objects.filter(requirement_id__customer_id=self.kwargs.get('customer_id'))
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
            queryset = self.get_queryset()
            if request.accepted_renderer.format == 'html':
                context = {'quotation_list': queryset,
                'customer_id': customer_id,
                'customer_data':customer_data}  # Pass the list of customers with counts to the template
                return render_html_response(context, self.template_name)
        else:
            messages.error(request, "You are not authorized to perform this action")
            return redirect(reverse('view_customer_list_quotation'))