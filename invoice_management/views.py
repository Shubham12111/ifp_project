import json
from itertools import chain

from django.contrib import messages

from rest_framework import generics, status
from rest_framework.renderers import TemplateHTMLRenderer, JSONRenderer

from requirement_management.models import SORItem
from requirement_management.quotation_views import DecimalEncoder

from customer_management.models import BillingAddress

from infinity_fire_solutions.permission import *
from infinity_fire_solutions.response_schemas import create_api_response, render_html_response, convert_serializer_errors

from invoice_management.serializers import (
    InvoiceCreateSerializer,
    InvoiceListSerializer,
    InvoiceStatusUpdateSerializer,

    # models
    Invoice,

    # Helper Forgien models
    Quotation
)


def get_customer_data(customer_id):

    """
    Get customer data by customer ID.

    Args:
        customer_id (int): The ID of the customer.

    Returns:
        User: The customer data if found, otherwise None.
    """
    if not customer_id:
        return None
    
    customer_data = User.objects.filter(id=customer_id, is_active=True,
                                        roles__name__icontains='customer').first()
    
    return customer_data

class ShowInvoiceView(CustomAuthenticationMixin, generics.GenericAPIView):

    renderer_classes = [TemplateHTMLRenderer,JSONRenderer]
    template_name = 'invoice_view.html'
    ordering_fields = ['created_at']
    queryset = Invoice.objects.all()
    serializer_class = InvoiceListSerializer

    def get_object(self, customer: User) -> Invoice:
        instance = None
        invoice_id = self.kwargs.get('pk', None)

        if invoice_id and customer:
            queryset = super().get_queryset()
            instance = queryset.filter(
                pk=invoice_id,
                customer=customer,
            ).first()

        return instance
    
    def get_customer_billing_address(self, customer: User) -> BillingAddress:

        if not customer:
            return None
        
        instance = BillingAddress.objects.filter(
            user_id=customer
        ).first()

        return instance
    
    def get(self, request, *args, **kwargs):
        authenticated_user, data_access_value = check_authentication_and_permissions(
           self,"fire_risk_assessment", HasCreateDataPermission, 'detail'
        )
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect

        customer_id = kwargs.get('customer_id', None)
        customer = get_customer_data(customer_id)

        if not customer:
            messages.error(request, "You are not authorized to perform this action")
            return redirect(reverse('customer_list'))

        customer_billing_address = self.get_customer_billing_address(customer)
        
        instance = self.get_object(customer)
        if not instance:
            messages.error(request, "You are not authorized to perform this action")
            return redirect(reverse('cs_customer_invoice_list', kwargs={'customer_id': kwargs.get('customer_id')}))


        # Create the context for the template
        context= {
            'customer_id': customer_id,
            'customer_data': customer,
            'customer_address': customer_billing_address,
            'requirement_instance': instance.requirement,
            'quotation': instance.quotation,
            'instance': instance
        }

        # This method handles GET requests for updating an existing Requirement object.
        if request.accepted_renderer.format == 'html':
            return render_html_response(context, self.template_name or 'invoice_view.html')
        else:
            messages.error(request, "You are not authorized to perform this action")
            return redirect(reverse('cs_customer_invoice_list', kwargs={'customer_id': kwargs.get('customer_id')}))


class CreateInvoiceView(CustomAuthenticationMixin,generics.GenericAPIView):
    
    renderer_classes = [TemplateHTMLRenderer,JSONRenderer]
    template_name = 'invoice_add_edit.html'
    ordering_fields = ['created_at']
    queryset = Quotation.objects.all()
    serializer_class = InvoiceCreateSerializer

    def get_object(self, customer: User) -> Quotation:
        instance = None
        quotation_id = self.kwargs.get('quotation_id', None)

        if quotation_id and customer:
            queryset = super().get_queryset()
            instance = queryset.filter(
                pk=quotation_id,
                customer_id=customer,
                job__status='completed',
                job__isnull=False,
                invoice__isnull=True
            ).first()

        return instance
    
    def get_customer_billing_address(self, customer: User) -> BillingAddress:

        if not customer:
            return None
        
        instance = BillingAddress.objects.filter(
            user_id=customer
        ).first()

        return instance

    def get(self, request, *args, **kwargs):
        authenticated_user, data_access_value = check_authentication_and_permissions(
           self,"fire_risk_assessment", HasCreateDataPermission, 'detail'
        )
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect

        customer_id = kwargs.get('customer_id', None)
        customer = get_customer_data(customer_id)

        if not customer:
            messages.error(request, "You are not authorized to perform this action")
            return redirect(reverse('customer_list'))

        customer_billing_address = self.get_customer_billing_address(customer)
        
        instance = self.get_object(customer)
        if not instance:
            messages.error(request, "You are not authorized to perform this action")
            return redirect(reverse('cs_customer_quote_list', kwargs={'customer_id': kwargs.get('customer_id')}))

        customer_sors = SORItem.objects.filter(customer_id=customer).values('id','name','reference_number', 'category_id__name', 'price',)
        if not customer_sors:
            customer_sors = SORItem.objects.filter(customer_id__isnull=True).values('id','name','reference_number', 'category_id__name', 'price',)

        # Convert the queryset of dictionaries to a list
        customer_sors_list = list(customer_sors)

        # Serialize the list to JSON
        customer_sors_json = json.dumps(customer_sors_list, cls=DecimalEncoder)

        # Determine the report_instance based on quotation_data or the queryset
        report_instance = instance.report_id if instance.report_id else None

        # Retrieve the associated Requirement instance
        requirement_instance = instance.requirement_id if instance.requirement_id else report_instance.requirement_id if report_instance.requirement_id else None

        # Retrieve all associated Defect instances
        requiremnt_defect_instances = instance.defect_id.all() if instance.defect_id.exists() else report_instance.defect_id.all() if report_instance.defect_id.exists() else []

        # This method handles GET requests for updating an existing Requirement object.
        if request.accepted_renderer.format == 'html':
            context = {
                'requirement_instance': requirement_instance,  
                'report_instance':report_instance,
                'requiremnt_defect_instances': requiremnt_defect_instances,

                'customer_id': customer_id,
                'customer_data': customer,
                'customer_address': customer_billing_address,
                
                'all_sors': customer_sors_json,
                'quotation_data': instance
                }
            return render_html_response(context, self.template_name or 'invoice_add_edit.html')
        else:
            messages.error(request, "You are not authorized to perform this action")
            return redirect(reverse('cs_customer_quote_list', kwargs={'customer_id': kwargs.get('customer_id')}))

    def post(self, request, *args, **kwargs):
        authenticated_user, data_access_value = check_authentication_and_permissions(
           self,"fire_risk_assessment", HasCreateDataPermission, 'detail'
        )
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect
        
        customer_id = kwargs.get('customer_id', None)
        customer = get_customer_data(customer_id)

        if not customer:
            messages.error(request, "You are not authorized to perform this action")
            return redirect(reverse('customer_list'))

        customer_billing_address = self.get_customer_billing_address(customer)
        
        instance = self.get_object(customer)
        if not instance:
            messages.error(request, "You are not authorized to perform this action")
            return redirect(reverse('cs_customer_quote_list', kwargs={'customer_id': kwargs.get('customer_id')}))
        
        defects_list = request.data.get('defectList', [])

        sor_items_dict = {}
        
        defect_sor_values = request.data.get('defectSorValues', {})
        if defect_sor_values:
            sor_id_list = list(
                chain.from_iterable(
                    filter(
                        None, 
                        map(
                            lambda key: map(
                                lambda sub_key: defect_sor_values[key][sub_key].get('sor-id', None), defect_sor_values[key]
                            ), 
                            defect_sor_values
                        )
                    )
                )
            )

            # Fetch SORItem objects based on 'sor-id'
            sor_items = SORItem.objects.filter(id__in=sor_id_list).all() if sor_id_list else None

            # Convert SORItem objects to dictionaries
            sor_items_data = {item.id: item.to_dict() for item in sor_items} if sor_items else {}

            # Populate the 'sor_items' data under each 'sor-id' key
            sor_items_dict = {
                defect_id: {
                    unique_key: {
                        'sor-id': sor_item.get('sor-id', None),
                        'price': float(sor_item.get('price')),
                        'total_price': float(sor_item.get('price')) * int(sor_item.get('quantity', 1)),
                        'quantity': int(sor_item.get('quantity', 1)),
                        'sor_items': sor_items_data.get(int(sor_item.get('sor-id', None)), [])  # Reference 'sor_items_data' using the 'sor-id'
                    }
                    for unique_key, sor_item in sor_data.items() if sor_item.get('sor-id', None)
                }
                for defect_id, sor_data in defect_sor_values.items()
            }

        # Create a dictionary to store the final JSON data
        json_data = {
            'status': f'{request.data.get("status", "draft")}',
            'defectSorValues': sor_items_dict,
            'defectList': defects_list,
        }

        data = {
            "requirement": instance.requirement_id.id,
            "report": instance.report_id.id,
            "defects": defects_list,
            "quotation": instance.id,
            "invoice_json": json_data,
            "total_amount": request.data.get('total_amount', 0),
            "status": f'{request.data.get("status", "draft")}',

            **({"billing_information_json": customer_billing_address.id} if customer_billing_address else {})
        }

        serializer = self.get_serializer(data=data)
        if serializer.is_valid():
            invoice = serializer.save(
                user=request.user,
                customer=customer
            )
            
            messages.success(request, 'Invoice has been created successfully!')
            return create_api_response(
                status_code=status.HTTP_201_CREATED,
                message='Invoice has been created successfully!'
            )

        return create_api_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            message='Unable to submit your data, please validate it once befor submitting.',
            data=convert_serializer_errors(serializer.errors)
        )

class EditInvoiceView(CustomAuthenticationMixin, generics.GenericAPIView):

    renderer_classes = [TemplateHTMLRenderer,JSONRenderer]
    template_name = 'invoice_add_edit.html'
    ordering_fields = ['created_at']
    queryset = Invoice.objects.all()
    serializer_class = InvoiceCreateSerializer

    def get_object(self, customer: User) -> Invoice:
        instance = None
        invoice_id = self.kwargs.get('pk', None)

        if invoice_id and customer:
            queryset = super().get_queryset()
            instance = queryset.filter(
                pk=invoice_id,
                customer=customer,
                status='draft'
            ).first()

        return instance
    
    def get_customer_billing_address(self, customer: User) -> BillingAddress:

        if not customer:
            return None
        
        instance = BillingAddress.objects.filter(
            user_id=customer
        ).first()

        return instance
    
    def get(self, request, *args, **kwargs):
        authenticated_user, data_access_value = check_authentication_and_permissions(
           self,"fire_risk_assessment", HasCreateDataPermission, 'detail'
        )
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect

        customer_id = kwargs.get('customer_id', None)
        customer = get_customer_data(customer_id)

        if not customer:
            messages.error(request, "You are not authorized to perform this action")
            return redirect(reverse('customer_list'))

        customer_billing_address = self.get_customer_billing_address(customer)
        
        instance = self.get_object(customer)
        if not instance:
            messages.error(request, "You are not authorized to perform this action")
            return redirect(reverse('cs_customer_invoice_list', kwargs={'customer_id': kwargs.get('customer_id')}))

        customer_sors = SORItem.objects.filter(customer_id=customer).values('id','name','reference_number', 'category_id__name', 'price',)
        if not customer_sors:
            customer_sors = SORItem.objects.filter(customer_id__isnull=True).values('id','name','reference_number', 'category_id__name', 'price',)

        # Convert the queryset of dictionaries to a list
        customer_sors_list = list(customer_sors)

        # Serialize the list to JSON
        customer_sors_json = json.dumps(customer_sors_list, cls=DecimalEncoder)

        # Determine the report_instance based on quotation_data or the queryset
        report_instance = instance.report if instance.report else None

        # Retrieve the associated Requirement instance
        requirement_instance = instance.requirement if instance.requirement else report_instance.requirement_id if report_instance.requirement_id else None

        # Retrieve all associated Defect instances
        requiremnt_defect_instances = instance.defects.all() if instance.defects.exists() else report_instance.defect_id.all() if report_instance.defect_id.exists() else []

        # This method handles GET requests for updating an existing Requirement object.
        if request.accepted_renderer.format == 'html':
            context = {
                'requirement_instance': requirement_instance,  
                'report_instance':report_instance,
                'requiremnt_defect_instances': requiremnt_defect_instances,

                'customer_id': customer_id,
                'customer_data': customer,
                'customer_address': customer_billing_address,
                
                'all_sors': customer_sors_json,
                'invoice_data': instance
                }
            return render_html_response(context, self.template_name or 'invoice_add_edit.html')
        else:
            messages.error(request, "You are not authorized to perform this action")
            return redirect(reverse('cs_customer_invoice_list', kwargs={'customer_id': kwargs.get('customer_id')}))

    def post(self, request, *args, **kwargs):
        authenticated_user, data_access_value = check_authentication_and_permissions(
           self,"fire_risk_assessment", HasCreateDataPermission, 'detail'
        )
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect
        
        customer_id = kwargs.get('customer_id', None)
        customer = get_customer_data(customer_id)

        if not customer:
            messages.error(request, "You are not authorized to perform this action")
            return redirect(reverse('customer_list'))

        customer_billing_address = self.get_customer_billing_address(customer)
        
        instance = self.get_object(customer)
        if not instance:
            messages.error(request, "You are not authorized to perform this action")
            return redirect(reverse('cs_customer_invoice_list', kwargs={'customer_id': kwargs.get('customer_id')}))
        
        defects_list = request.data.get('defectList', [])

        sor_items_dict = {}
        
        defect_sor_values = request.data.get('defectSorValues', {})
        if defect_sor_values:
            sor_id_list = list(
                chain.from_iterable(
                    filter(
                        None, 
                        map(
                            lambda key: map(
                                lambda sub_key: defect_sor_values[key][sub_key].get('sor-id', None), defect_sor_values[key]
                            ), 
                            defect_sor_values
                        )
                    )
                )
            )

            # Fetch SORItem objects based on 'sor-id'
            sor_items = SORItem.objects.filter(id__in=sor_id_list).all() if sor_id_list else None

            # Convert SORItem objects to dictionaries
            sor_items_data = {item.id: item.to_dict() for item in sor_items} if sor_items else {}

            # Populate the 'sor_items' data under each 'sor-id' key
            sor_items_dict = {
                defect_id: {
                    unique_key: {
                        'sor-id': sor_item.get('sor-id', None),
                        'price': float(sor_item.get('price')),
                        'total_price': float(sor_item.get('price')) * int(sor_item.get('quantity', 1)),
                        'quantity': int(sor_item.get('quantity', 1)),
                        'sor_items': sor_items_data.get(int(sor_item.get('sor-id', None)), [])  # Reference 'sor_items_data' using the 'sor-id'
                    }
                    for unique_key, sor_item in sor_data.items() if sor_item.get('sor-id', None)
                }
                for defect_id, sor_data in defect_sor_values.items()
            }

        # Create a dictionary to store the final JSON data
        json_data = {
            'status': f'{request.data.get("status", "draft")}',
            'defectSorValues': sor_items_dict,
            'defectList': defects_list,
        }

        data = {
            "requirement": instance.requirement.id,
            "report": instance.report.id,
            "defects": defects_list,
            "quotation": instance.quotation.id,
            "invoice_json": json_data,
            "total_amount": request.data.get('total_amount', 0),
            "status": f'{request.data.get("status", "draft")}',

            **({"billing_information_json": customer_billing_address.id} if customer_billing_address else {})
        }

        serializer = self.get_serializer(data=data, instance=instance)
        if serializer.is_valid():
            invoice = serializer.update(
                instance,
                serializer.validated_data
            )
            
            messages.success(request, 'Invoice has been updated successfully!')
            return create_api_response(
                status_code=status.HTTP_201_CREATED,
                message='Invoice has been updated successfully!'
            )

        return create_api_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            message='Unable to submit your data, please validate it once befor submitting.',
            data=convert_serializer_errors(serializer.errors)
        )

class DeleteInvoiceView(CustomAuthenticationMixin, generics.GenericAPIView):

    renderer_classes = [TemplateHTMLRenderer,JSONRenderer]
    template_name = 'invoice_add_edit.html'
    ordering_fields = ['created_at']
    queryset = Invoice.objects.all()
    serializer_class = InvoiceCreateSerializer

    def get_object(self, customer: User) -> Invoice:
        instance = None
        invoice_id = self.kwargs.get('pk', None)

        if invoice_id and customer:
            queryset = super().get_queryset()
            instance = queryset.filter(
                pk=invoice_id,
                customer=customer,
                status='draft'
            ).first()

        return instance
    
    def delete(self, request, *args, **kwargs):
        authenticated_user, data_access_value = check_authentication_and_permissions(
           self,"fire_risk_assessment", HasCreateDataPermission, 'detail'
        )
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect

        customer_id = kwargs.get('customer_id', None)
        customer = get_customer_data(customer_id)

        if not customer:
            messages.error(request, "You are not authorized to perform this action")
            return redirect(reverse('customer_list'))
        
        instance = self.get_object(customer)
        if not instance:
            messages.error(request, "You are not authorized to perform this action")
            return redirect(reverse('cs_customer_invoice_list', kwargs={'customer_id': kwargs.get('customer_id')}))

        instance.delete()

        # This method handles GET requests for updating an existing Requirement object.
        if request.accepted_renderer.format == 'html':
            messages.success(request, "Invoice has been deleted Successfully.")
            return redirect(reverse('cs_customer_invoice_list', kwargs={'customer_id': kwargs.get('customer_id')}))
        else:
            messages.error(request, "You are not authorized to perform this action")
            return redirect(reverse('cs_customer_invoice_list', kwargs={'customer_id': kwargs.get('customer_id')}))

class MarkAsPaidInvoiceView(CustomAuthenticationMixin, generics.GenericAPIView):

    renderer_classes = [TemplateHTMLRenderer,JSONRenderer]
    queryset = Invoice.objects.all()
    serializer_class = InvoiceStatusUpdateSerializer

    def get_object(self, customer: User) -> Invoice:
        instance = None
        invoice_id = self.kwargs.get('pk', None)

        if invoice_id and customer:
            queryset = super().get_queryset()
            instance = queryset.filter(
                pk=invoice_id,
                customer=customer,
                status__in=['submitted', 'sent_to_customer']
            ).first()

        return instance
    
    def get(self, request, *args, **kwargs):
        authenticated_user, data_access_value = check_authentication_and_permissions(
           self,"fire_risk_assessment", HasCreateDataPermission, 'detail'
        )
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect

        customer_id = kwargs.get('customer_id', None)
        customer = get_customer_data(customer_id)

        if not customer:
            messages.error(request, "You are not authorized to perform this action")
            return redirect(reverse('customer_list'))
        
        instance = self.get_object(customer)
        if not instance:
            messages.error(request, "You are not authorized to perform this action")
            return redirect(reverse('cs_customer_invoice_list', kwargs={'customer_id': kwargs.get('customer_id')}))
        
        data = {
            'status': 'paid'
        }

        serializer = self.get_serializer(
            data=data,
            instance=instance
        )

        if serializer.is_valid():
            invoice = serializer.update(
                instance,
                serializer.validated_data
            )
        
            messages.success(request, "Invoice is paid successfully!")
            return redirect(reverse('cs_customer_invoice_list', kwargs={'customer_id': kwargs.get('customer_id')}))

        messages.error(request, "You are not authorized to perform this action")
        return redirect(reverse('cs_customer_invoice_list', kwargs={'customer_id': kwargs.get('customer_id')}))

class SendInvoiceToCustomerView(CustomAuthenticationMixin, generics.GenericAPIView):

    renderer_classes = [TemplateHTMLRenderer,JSONRenderer]
    queryset = Invoice.objects.all()
    serializer_class = InvoiceStatusUpdateSerializer

    def get_object(self, customer: User) -> Invoice:
        instance = None
        invoice_id = self.kwargs.get('pk', None)

        if invoice_id and customer:
            queryset = super().get_queryset()
            instance = queryset.filter(
                pk=invoice_id,
                customer=customer,
                status__in=['submitted', 'sent_to_customer', 'paid']
            ).first()

        return instance
    
    def get(self, request, *args, **kwargs):
        authenticated_user, data_access_value = check_authentication_and_permissions(
           self,"fire_risk_assessment", HasCreateDataPermission, 'detail'
        )
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect

        customer_id = kwargs.get('customer_id', None)
        customer = get_customer_data(customer_id)

        if not customer:
            messages.error(request, "You are not authorized to perform this action")
            return redirect(reverse('customer_list'))
        
        instance = self.get_object(customer)
        if not instance:
            messages.error(request, "You are not authorized to perform this action")
            return redirect(reverse('cs_customer_invoice_list', kwargs={'customer_id': kwargs.get('customer_id')}))
        
        data = {
            'status': 'sent_to_customer'
        }

        serializer = self.get_serializer(
            data=data,
            instance=instance
        )

        if serializer.is_valid():
            invoice = serializer.update(
                instance,
                serializer.validated_data
            )
        
            messages.success(request, "Invoice sent to the customer successfully!")
            return redirect(reverse('cs_customer_invoice_list', kwargs={'customer_id': kwargs.get('customer_id')}))

        messages.error(request, "You are not authorized to perform this action")
        return redirect(reverse('cs_customer_invoice_list', kwargs={'customer_id': kwargs.get('customer_id')}))