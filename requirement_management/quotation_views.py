from infinity_fire_solutions.aws_helper import *
from infinity_fire_solutions.permission import *
from infinity_fire_solutions.response_schemas import create_api_response, render_html_response
from rest_framework import generics, status
from rest_framework.renderers import TemplateHTMLRenderer, JSONRenderer
from .quotation_serializers import *
from rest_framework import filters
from infinity_fire_solutions.email import *
from .models import Requirement, Report, SORItem
from django.contrib import messages


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
        all_fra = Requirement.objects.filter()
        
        customers_with_counts = []  # Create a list to store customer objects with counts

        for customer in queryset:
            fra_counts = all_fra.filter(customer_id=customer).count()
            customers_with_counts.append({'customer': customer, 'fra_counts': fra_counts})

        if request.accepted_renderer.format == 'html':
            context = {'customers_with_counts': customers_with_counts}  # Pass the list of customers with counts to the template
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

            queryset = Report.objects.filter(requirement_id__customer_id=self.kwargs.get('customer_id'))
            return queryset

    def get(self, request, *args, **kwargs):
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self, "fire_risk_assessment", HasListDataPermission, 'list'
        )
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect

        queryset = self.get_queryset()
        # breakpoint()
        if request.accepted_renderer.format == 'html':
            context = {'report_list': queryset}  # Pass the list of customers with counts to the template
            return render_html_response(context, self.template_name)
        else:
            serializer = self.serializer_class(queryset, many=True)
            return create_api_response(status_code=status.HTTP_200_OK,
                                    message="Data retrieved",
                                    data=serializer.data)


from django.forms import modelformset_factory
from customer_management.models import *

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

        customer_data = User.objects.filter(id=kwargs.get('customer_id')).first()
        if customer_data:
            report_id = kwargs.get('pk')
            # This method handles GET requests for updating an existing Requirement object.
            if request.accepted_renderer.format == 'html':
                report_instance = self.get_queryset()
                
                requirement_instance = report_instance.requirement_id
                requiremnt_defect_instances = report_instance.defect_id.all()
                all_sors = SORItem.objects.all()
                if report_instance:

                    context = {
                        'requirement_instance': requirement_instance,  
                        'report_instance':report_instance,
                        'requiremnt_defect_instances': requiremnt_defect_instances,
                        'customer_id': kwargs.get('customer_id'),
                        'customer_data':customer_data,
                        'all_sors': all_sors
                        }
            

                    return render_html_response(context, self.template_name)
                else:
                    messages.error(request, "You are not authorized to perform this action")
                    return redirect(reverse('customer_requirement_list', kwargs={'customer_id': kwargs.get('customer_id')}))
        else:
            messages.error(request, "You are not authorized to perform this action")
            return redirect(reverse('customer_requirement_list', kwargs={'customer_id': kwargs.get('customer_id')}))

