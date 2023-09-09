from django.shortcuts import render, redirect
from infinity_fire_solutions.aws_helper import *
from infinity_fire_solutions.permission import *
from infinity_fire_solutions.response_schemas import create_api_response, convert_serializer_errors, render_html_response
from rest_framework import generics, status
from rest_framework.renderers import TemplateHTMLRenderer, JSONRenderer
from .serializers import *
from .models import Requirement, RequirementDefect,RequirementDefectDocument, RequirementAsset
from django.contrib import messages
from rest_framework.response import Response
from rest_framework import filters
from drf_yasg.utils import swagger_auto_schema
from infinity_fire_solutions.utils import docs_schema_response_new
from django.http import JsonResponse
import ast
import os
import pdfkit
from django.template.loader import render_to_string
from infinity_fire_solutions.email import *



def get_customer_data(customer_id):
    customer_data = User.objects.filter(id=customer_id).first()
    
    return customer_data

def get_selected_defect_data(request, customer_id, pk):
    if request.method == 'POST':
        selected_defect_ids = request.POST.getlist('selectedDefectIds')
        # Query RequirementDefect objects related to the customer and requirement
        requirement_defect = RequirementDefect.objects.filter(
            requirement_id=pk, requirement_id__customer_id=customer_id, pk__in =selected_defect_ids
        )

        # Create a list to store serialized defect data
        defect_data = []

        from django.core import serializers


        for defect in requirement_defect:
            # Serialize the defect data (excluding images)
            defect_json = serializers.serialize('json', [defect])
            
            defect_data.append({
                'defect': defect_json,  # Assuming 'defect_json' is a list with one item
            })

        # Create a JSON response containing all the defect data
        response_data = {'defects': defect_data}
        return JsonResponse(response_data, safe=False)



def requirement_image(requirement_instance):
    document_paths = []
    
    for document in RequirementAsset.objects.filter(requirement_id=requirement_instance):
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
    
    

def filter_requirements(data_access_value, user, customer=None):
    # Define a mapping of data access values to corresponding filters.
    filter_mapping = {
        "self": Q(user_id=user),
        "all": Q(),  # An empty Q() object returns all data.
    }

    if customer:
        queryset = Requirement.objects.filter(customer_id=customer)
    else: queryset = Requirement.objects.all()
    
    if user.roles.name == "quantity_surveyor":
        queryset =  queryset.filter(
            Q(quantity_surveyor=user)|Q(user_id=user) | filter_mapping.get(data_access_value, Q())
        )
    elif user.roles.name == "surveyor":
        queryset = queryset.filter(
            Q(surveyor=user)|Q(user_id=user) | filter_mapping.get(data_access_value, Q())
        )
    else:
        queryset = queryset.filter(filter_mapping.get(data_access_value, Q()))
    return queryset 

class RequirementCustomerListView(CustomAuthenticationMixin,generics.ListAPIView):
    
    serializer_class = RequirementCustomerSerializer
    renderer_classes = [TemplateHTMLRenderer,JSONRenderer]
    filter_backends = [filters.SearchFilter]
    search_fields = ['customer_id__first_name', 'customer_id__last_name']
    template_name = 'requirement_customer_list.html'
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


class RequirementListView(CustomAuthenticationMixin,generics.ListAPIView):
    """
    View to get the listing of all requirements.
    Supports both HTML and JSON response formats.
    """
    serializer_class = RequirementSerializer
    renderer_classes = [TemplateHTMLRenderer,JSONRenderer]
    filter_backends = [filters.SearchFilter]
    search_fields = ['customer_id__first_name', 'customer_id__last_name']
    template_name = 'requirement_list.html'
    ordering_fields = ['created_at'] 

    common_get_response = {
    status.HTTP_200_OK: 
        docs_schema_response_new(
            status_code=status.HTTP_200_OK,
            serializer_class=serializer_class,
            message = "Data retrieved",
            )
    }
    
    @swagger_auto_schema(operation_id='Requirement Listing', responses={**common_get_response})
    def get(self, request, *args, **kwargs):

        """
        Handle both AJAX (JSON) and HTML requests.
        """
        customer_id = kwargs.get('customer_id', None)
        
        customer_data = User.objects.filter(id=customer_id).first()
        
        if customer_data:
            # Call the handle_unauthenticated method to handle unauthenticated access.
            authenticated_user, data_access_value = check_authentication_and_permissions(
                self,"fire_risk_assessment", HasListDataPermission, 'list'
            )
            if isinstance(authenticated_user, HttpResponseRedirect):
                return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect

            queryset = filter_requirements(data_access_value, self.request.user, customer_data)
            qs_role = UserRole.objects.filter(name='quantity_surveyor')
            quantity_sureveyors = User.objects.filter(roles__in=qs_role)
            
            sureveyors = User.objects.filter(roles__name='surveyor')
            

            if request.accepted_renderer.format == 'html':
                context = {'requirements':queryset, 'customer_id':customer_id,
                        'quantity_sureveyors': quantity_sureveyors,
                        'customer_data':customer_data,
                        'sureveyors':sureveyors}
                return render_html_response(context,self.template_name)
            else:
                serializer = self.serializer_class(queryset, many=True)
                return create_api_response(status_code=status.HTTP_200_OK,
                                                message="Data retrieved",
                                                data=serializer.data)
        else:
            messages.error(request, "You are not authorized to perform this action")
            return redirect(reverse('customer_requirement_list', kwargs={'customer_id': customer_id}))  
        
        
        
class RequirementAddView(CustomAuthenticationMixin, generics.CreateAPIView):
    """
    View for adding  a requirement.
    Supports both HTML and JSON response formats.
    """
    serializer_class = RequirementAddSerializer
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'requirement.html'
    
    @swagger_auto_schema(auto_schema=None) 
    def get(self, request, *args, **kwargs):
        """
        Handle GET request to display a form for adding a requirement.
        If the requirement exists, retrieve the serialized data and render the HTML template.
        If the requirement does not exist, render the HTML template with an empty serializer.
        """
        customer_id = kwargs.get('customer_id', None)
        
        customer_data = User.objects.filter(id=customer_id).first()
        
        if customer_data:
            # Call the handle_unauthenticated method to handle unauthenticated access
            authenticated_user, data_access_value = check_authentication_and_permissions(
            self,"fire_risk_assessment", HasCreateDataPermission, 'add'
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
            return redirect(reverse('customer_requirement_list', kwargs={'customer_id': customer_id}))

  
    def post(self, request, *args, **kwargs):
        """
        Handle POST request to add a requirement.
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
            
            message = "Congratulations! your requirement has been added successfully."
            if serializer.is_valid():
                serializer.validated_data['user_id'] = request.user  # Assign the current user instance.
                serializer.validated_data['customer_id'] = customer_data
                serializer.save()

                if request.accepted_renderer.format == 'html':
                    messages.success(request, message)
                    return redirect(reverse('customer_requirement_list', kwargs={'customer_id': customer_id}))

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
            return redirect(reverse('customer_requirement_list', kwargs={'customer_id': customer_id}))  

class RequirementDetailView(CustomAuthenticationMixin, generics.RetrieveAPIView):
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'requirement_detail.html'
    serializer_class = RequirementAddSerializer
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
                html_content = render_to_string('report_detail.html', context)

                # create the PDF file for the invoice
                pdfkit.from_string(html_content, output_file, options=self.pdf_options)
                
            except Exception as e:
                # Handle any exceptions that occur during PDF generation
                print("error")

        return output_file
    
    def get_queryset(self):
        """
        Get the queryset for listing Requirement items.

        Returns:
            QuerySet: A queryset of Requirements items filtered based on the authenticated user's ID.
        """
        # Get the model class using the provided module_name string
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self, "fire_risk_assessment", HasViewDataPermission, 'view'
        )
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect

        queryset = filter_requirements(data_access_value, self.request.user, customer=self.kwargs.get('customer_id'))
        queryset =  queryset.filter(pk=self.kwargs.get('pk')).first()
        

        return queryset

    @swagger_auto_schema(auto_schema=None)
    def get(self, request, *args, **kwargs):
        customer_id = kwargs.get('customer_id')
        customer_data = User.objects.filter(id=customer_id).first()
        
        if customer_data:
            # This method handles GET requests for updating an existing Requirement object.
            if request.accepted_renderer.format == 'html':
                instance = self.get_queryset()
                if instance:
                    document_paths = []
                    requirement_defect = RequirementDefect.objects.filter(requirement_id=instance.id)
                    serializer = self.serializer_class(instance=instance, context={'request': request})
                    
                    
                    document_paths = requirement_image(instance)
                            
                    # Retrieve users associated with these roles
                    users_with_survey_permission = User.objects.filter(roles__name= "surveyor")
                    
                    context = {
                        'serializer': serializer, 
                        'requirement_instance': instance, 
                        'requirement_defect': requirement_defect, 
                        'document_paths': document_paths,
                        'surveyers': users_with_survey_permission,
                        'customer_id': kwargs.get('customer_id'),
                        'customer_data':customer_data
                        }
               

                    return render_html_response(context, self.template_name)
            else:
                messages.error(request, "You are not authorized to perform this action")
                return redirect(reverse('customer_requirement_list', kwargs={'customer_id': kwargs.get('customer_id')}))
            
    def post(self, request, *args, **kwargs):
        instance = self.get_queryset()
        try:
            import base64
            import os
            
            
            data = request.POST
            # Extract the relevant fields from the data
            comments = data.get('comments', '')
            
            signature_data_url = data.get('signature_data', '')

            if signature_data_url:
                # Extract the base64-encoded data from the data URL
                _, base64_data = signature_data_url.split(',')
                image_data = base64.b64decode(base64_data)
                
                # Generate a unique filename for the image
                unique_filename = f"{str(uuid.uuid4())}.png"

                # Save the image to a temporary directory (e.g., /tmp/)
                temp_dir = '/tmp/'
                image_path = os.path.join(temp_dir, unique_filename)
                
                with open(image_path, 'wb') as img_file:
                    img_file.write(image_data)
                # Optionally, upload the image to S3
                try:
                    signature_path = f'requirement/{instance.id}/report'
                    upload_signature_to_s3(unique_filename, image_path,signature_path)
                    signature_path = f'requirement/{instance.id}/report/{unique_filename}'
                    
                except Exception as e:
                    print(f"An error occurred: {str(e)}")
                    return False
            else:
                signature_path = ""
                
                
            # Assuming you also have a requirement_id and defect_id in your data
            defect_ids = data.get('selected_defect_ids', [])
            
            # Create a new Report instance and save it to the database
            report = Report(
                requirement_id=instance,
                comments=comments,
                signature_path = signature_path,
                user_id=request.user,
                status=request.POST.get('status')
                
            )
            
            report.save()
            
            report.defect_id.set(RequirementDefect.objects.filter(pk__in=defect_ids.split(',')))
            
            if request.POST.get('status') == "submit":
                all_report_defects = report.defect_id.all()
               
                requirement_document_images = RequirementAsset.objects.filter(requirement_id=instance.id)
                requirement_document_images_serializer = RequirementAssetSerializer(requirement_document_images, many=True)

                requirement_defect_images = RequirementDefectDocument.objects.filter(defect_id__in=all_report_defects)
                requirement_defect_images_serializer = RequirementDefectDocumentSerializer(requirement_defect_images, many=True)

                
                if report.signature_path:
                    signature_data_url = generate_presigned_url(report.signature_path)
                else:
                    signature_data_url = ""
                    
                context = {
                    'requirement_instance': instance,
                    'requirement_defects': all_report_defects,
                    'requirement_images': requirement_document_images_serializer.data,
                    'requirement_defect_images': requirement_defect_images_serializer.data,
                    'comment': report.comments,
                    'signature_data_url':signature_data_url,
                }
                
                unique_pdf_filename = f"{str(uuid.uuid4())}_report_{report.id}.pdf"
                
                pdf_file = self.save_pdf_from_html(context=context, file_name=unique_pdf_filename)
                pdf_path = f'requirement/{instance.id}/report/pdf'
                
               
                
                upload_signature_to_s3(unique_pdf_filename, pdf_file, pdf_path)
                
                report.pdf_path = f'requirement/{instance.id}/report/pdf/{unique_pdf_filename}'
                report.save()
                
                # send email to QS
                if instance.quantity_surveyor and instance.surveyor:
                    context = {'user': instance.quantity_surveyor,'surveyor': instance.surveyor,'site_url': get_site_url(request) }

                    email = Email()
                    email.send_mail(instance.quantity_surveyor.email, 'email_templates/report.html', context, "Submission of Survey Report")

                
                
            messages.success(request, "Congratulations! your requirement report has been added successfully. ")
            return create_api_response(status_code=status.HTTP_404_NOT_FOUND,
                                        message="Congratulations! your requirement report has been added successfully.", )
            
        except Exception as e:
            message = "Something went wrong"
            if request.accepted_renderer.format == 'html':
                messages.warning(request, message)
                return redirect(reverse('customer_requirement_view', kwargs={'pk':instance.id, 'customer_id':kwargs.get('customer_id')}))
            else:
                return create_api_response(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        message=message
                    )

class RequirementUpdateView(CustomAuthenticationMixin, generics.UpdateAPIView):
    """
    API view for updating a requirement.

    This view handles both HTML and API requests for updating a requirement instance.
    If the requirement instance exists, it will be updated with the provided data.
    Otherwise, an error message will be returned.

    The following request methods are supported:
    - POST: Updates the requirement instance.

    Note: Make sure to replace 'your_template_name.html' with the appropriate HTML template name.
    """
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'requirement.html'
    serializer_class = RequirementAddSerializer
    
    def get_queryset(self):
        """
        Get the queryset for listing Requirement items.

        Returns:
            QuerySet: A queryset of Requirements items filtered based on the authenticated user's ID.
        """
        # Get the model class using the provided module_name string
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self, "fire_risk_assessment", HasUpdateDataPermission, 'change'
        )
        if isinstance(authenticated_user, HttpResponseRedirect):
            return authenticated_user  # Redirect the user to the page specified in the HttpResponseRedirect

        queryset = filter_requirements(data_access_value, self.request.user, customer=self.kwargs.get('customer_id'))
        queryset = queryset.filter(pk=self.kwargs.get('pk')).first()
        return queryset

    @swagger_auto_schema(auto_schema=None)
    def get(self, request, *args, **kwargs):
        customer_id = self.kwargs.get('customer_id')
        customer_data = User.objects.filter(id=customer_id).first()
        # This method handles GET requests for updating an existing Requirement object.
        if request.accepted_renderer.format == 'html':
            instance = self.get_queryset()
            if instance:
                serializer = self.serializer_class(instance=instance, context={'request': request})
                context = {'serializer': serializer, 'requirement_instance': instance, 
                           'customer_id': self.kwargs.get('customer_id'),
                           'customer_data':customer_data}
                return render_html_response(context, self.template_name)
            else:
                messages.error(request, "You are not authorized to perform this action")
                return redirect(reverse('customer_requirement_list', kwargs={'customer_id': kwargs.get('customer_id')}))
    
    common_post_response = {
        status.HTTP_200_OK: 
            docs_schema_response_new(
                status_code=status.HTTP_200_OK,
                serializer_class=serializer_class,
                message = "Your Requirement has been updated successfully!",
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

    @swagger_auto_schema(operation_id='Requirement Edit', responses={**common_post_response})
    def post(self, request, *args, **kwargs):
        """
        Handle POST request to update a requirement instance.

        Args:
            request (rest_framework.request.Request): The HTTP request object.
            *args: Variable-length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            rest_framework.response.Response: HTTP response object.
                If successful, the requirement is updated, and the appropriate response is returned.
                If unsuccessful, an error response is returned.
        """
        instance = self.get_queryset()
        if instance:
            data = request.data
    
            file_list = data.getlist('file_list', [])
            
            if not any(file_list):
                data = data.copy()      # make a mutable copy of data before performing delete.
                del data['file_list']
            
            serializer_data = request.data if any(file_list) else data
            serializer_data['RBNO'] = instance.RBNO
            serializer_data['UPRN'] = instance.UPRN
            serializer = self.serializer_class(instance=instance, data=serializer_data, context={'request': request})


            if serializer.is_valid():
                # If the serializer data is valid, save the updated requirement instance.
                serializer.update(instance, validated_data=serializer.validated_data)
                message = "Your requirement has been updated successfully!"

                if request.accepted_renderer.format == 'html':
                    # For HTML requests, display a success message and redirect to customer_requirement_list.
                    messages.success(request, message)
                    return redirect(reverse('customer_requirement_edit', kwargs={'pk': instance.id, 'customer_id': kwargs.get('customer_id')}))
                else:
                    # For API requests, return a success response with serialized data.
                    return Response({'message': message, 'data': serializer.data}, status=status.HTTP_200_OK)
            else:
                if request.accepted_renderer.format == 'html':
                    # For HTML requests with invalid data, render the template with error messages.
                    context = {'serializer': serializer,
                     'requirement_instance': instance,'customer_id':kwargs.get('customer_id')}
                    return render(request, self.template_name, context)
                else:
                    # For API requests with invalid data, return an error response with serializer errors.
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            error_message = "You are not authorized to perform this action"
            if request.accepted_renderer.format == 'html':
                # For HTML requests with no instance, display an error message and redirect to customer_requirement_list.
                messages.error(request, error_message)
                return redirect(reverse('customer_requirement_list', kwargs={'customer_id': kwargs.get('customer_id')}))
            else:
                # For API requests with no instance, return an error response with an error message.
                return Response({'message': error_message}, status=status.HTTP_400_BAD_REQUEST)
            
class RequirementDeleteView(CustomAuthenticationMixin, generics.DestroyAPIView):
    """
    View for deleting a requirement.
    Supports both HTML and JSON response formats.
    """
    serializer_class = RequirementSerializer
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    
    common_delete_response = {
        status.HTTP_200_OK: 
            docs_schema_response_new(
                status_code=status.HTTP_200_OK,
                serializer_class=serializer_class,
                message = "Requirement has been deleted successfully!",
                ),
        status.HTTP_404_NOT_FOUND: 
            docs_schema_response_new(
                status_code=status.HTTP_404_NOT_FOUND,
                serializer_class=serializer_class,
                message = "Requirement not found OR You are not authorized to perform this action.",
                ),

    }
    @swagger_auto_schema(operation_id='Requirement Delete', responses={**common_delete_response})
    
    def delete(self, request, *args, **kwargs):
        """
        Handle DELETE request to delete a requirement.
        """
        authenticated_user, data_access_value = check_authentication_and_permissions(
            self, "fire_risk_assessment", HasUpdateDataPermission, 'delete'
        )

        # Get the requirement instance from the database.
        # Define a mapping of data access values to corresponding filters
        filter_mapping = {
            "self": Q(user_id=request.user ),
            "all": Q(),  # An empty Q() object returns all data
        }

        # Get the appropriate filter from the mapping based on the data access value,
        # or use an empty Q() object if the value is not in the mapping
        queryset = filter_requirements(data_access_value, self.request.user)
        instance = queryset.filter(pk=self.kwargs.get('pk')).first()

        if instance:
            # Proceed with the deletion
            instance.delete()
            messages.success(request, "Your requirement has been deleted successfully!")
            return create_api_response(status_code=status.HTTP_404_NOT_FOUND,
                                        message="Your requirement has been deleted successfully!", )
        else:
            messages.error(request, "Requirement not found OR You are not authorized to perform this action.")
            return create_api_response(status_code=status.HTTP_404_NOT_FOUND,
                                        message="Requirement not found OR You are not authorized to perform this action.", )
    
class RequirementDefectView(CustomAuthenticationMixin, generics.CreateAPIView):
    """
    View for adding  a requirement.
    Supports both HTML and JSON response formats.
    """
    # serializer_class = RequirementDefectAddSerializer
    serializer_class = RequirementDefectAddSerializer
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'defects.html'
    swagger_schema = None
    
    def get_queryset(self):
        """
        Get the filtered queryset for requirements based on the authenticated user.
        """
        authenticated_user, data_access_value = check_authentication_and_permissions(
           self,"fire_risk_assessment", HasCreateDataPermission, 'view'
        )
        
        queryset = filter_requirements(data_access_value, self.request.user, self.kwargs.get('customer_id'))
        queryset = queryset.filter(pk=self.kwargs.get('requirement_id')).first()
        
        return queryset
    
    def get_queryset_defect(self):
        """
        Get the filtered queryset for requirements based on the authenticated user.
        """
        queryset_defect = RequirementDefect.objects.filter(requirement_id = self.get_queryset() ).order_by('-created_at')
        return queryset_defect
    
    def get(self, request, *args, **kwargs):
        # This method handles GET requests for updating an existing Requirement object.
        requirement_instance = self.get_queryset()
        document_paths = requirement_image(requirement_instance)
        
        requirement_defects = self.get_queryset_defect()
        defect_instance = requirement_defects.filter(pk=self.kwargs.get('pk')).first()
        
        if defect_instance:
            serializer =  self.serializer_class(instance=defect_instance)
            
        else:
            serializer =  self.serializer_class()
            defect_instance = {}
        
        if request.accepted_renderer.format == 'html':
            context = {
                'serializer': serializer,
                'requirement_instance': requirement_instance,
                'defects_list': self.get_queryset_defect(),
                'defect_instance':defect_instance,
                'customer_id': kwargs.get('customer_id'),
                'document_paths':document_paths
                }
            return render_html_response(context, self.template_name)
        else:
            messages.error(request, "You are not authorized to perform this action")
            return redirect(reverse('customer_requirement_list', kwargs={'customer_id': kwargs.get('customer_id')}))  
        
    def post(self, request, *args, **kwargs):
        """
        Handle POST request to add a requirement.
        """
        # Call the handle_unauthenticated method to handle unauthenticated access.
        
        data = request.data
        
        file_list = data.getlist('file_list', [])
        
        requirement_instance = self.get_queryset()
        defect_instance = RequirementDefect.objects.filter(requirement_id = requirement_instance, pk=self.kwargs.get('pk')).first()
        
        if not any(file_list):
            data = data.copy()      # make a mutable copy of data before performing delete.
            del data['file_list']
        
        serializer_data = request.data if any(file_list) else data
        
        message = "Congratulations! your requirement defect has been added successfully."
        
        # Check if the site address instance exists for the customer
        if defect_instance:
            # If the site address instance exists, update it.
            serializer = self.serializer_class(data=serializer_data, instance=defect_instance, context={'request': request})
            message = "Your requirement defect has been updated successfully!"
        else: 
            # If the site address instance does not exist, create a new one.
            serializer = self.serializer_class(data=serializer_data, context={'request': request})
            message = "Your requirement defect has been added successfully!"
        
        
        if serializer.is_valid():
            if  not defect_instance:
                serializer.validated_data['requirement_id'] = requirement_instance
                serializer.save()
            else:
                serializer.update(defect_instance, validated_data=serializer.validated_data)

            if request.accepted_renderer.format == 'html':
                messages.success(request, message)
                return redirect(reverse('customer_requirement_view', kwargs={'customer_id': self.kwargs.get('customer_id'), 'pk':requirement_instance.id}))
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
                           'requirement_instance': requirement_instance,
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



  
class RequirementDefectDetailView(CustomAuthenticationMixin, generics.CreateAPIView):

    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'defect_detail.html'
    swagger_schema = None
    
    def get_queryset(self):
        """
        Get the filtered queryset for requirements based on the authenticated user.
        """
        queryset = RequirementDefect.objects.filter(pk=self.kwargs.get('defect_id')).order_by('-created_at')
        return queryset

    def get_requirement_instance(self):
        """
        Get the filtered queryset for requirements based on the authenticated user.
        """
        authenticated_user, data_access_value = check_authentication_and_permissions(
           self,"fire_risk_assessment", HasCreateDataPermission, 'view'
        )
        
        queryset = filter_requirements(data_access_value, self.request.user, self.kwargs.get('customer_id'))
        queryset = queryset.filter(pk=self.kwargs.get('requirement_id')).first()
        
        return queryset

    def get_documents(self):
        """
        Get the filtered document_paths.
        """
        document_paths = []
        
        defect_instance = self.get_queryset().first()
        for document in RequirementDefectDocument.objects.filter(defect_id=defect_instance):
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
        customer_id = self.kwargs.get('customer_id')

        customer_data = User.objects.filter(id=customer_id).first()
        if customer_data:
            defect_instance = self.get_queryset().first()
            requirement_instance = self.get_requirement_instance()
            document_paths = requirement_image(requirement_instance)
            
            if not defect_instance:
                messages.warning(request, "You are not authorized to perform this action")
                return redirect(reverse('customer_requirement_list', kwargs={'customer_id': self.kwargs.get('customer_id')}))  
            
            # Defect response doesn't exist, prepare context for displaying form
            context = {
                'defect_instance': defect_instance,
                'defect_document_paths':self.get_documents(),
                'defect_instance':defect_instance,
                'document_paths':document_paths,
                'customer_id':customer_id,
                'requirement_instance':requirement_instance,
                'customer_data':customer_data
            }

            return render_html_response(context, self.template_name)
        else:
            messages.warning(request, "You are not authorized to perform this action")
            return redirect(reverse('customer_requirement_list', kwargs={'customer_id': self.kwargs.get('customer_id')}))  

class RequirementDefectDeleteView(CustomAuthenticationMixin, generics.DestroyAPIView):
    """
    View for deleting a requirement.
    Supports both HTML and JSON response formats.
    """
    serializer_class = RequirementDefectSerializer
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    # permission_classes = [IsAuthenticated]
    template_name = 'defects.html'
    swagger_schema = None
    
    def delete(self, request, *args, **kwargs):
        """
        Handle DELETE request to delete a customer.
        """
        # Get the customer instance from the database
        # Call the handle_unauthenticated method to handle unauthenticated access

        authenticated_user, data_access_value = check_authentication_and_permissions(
            self,"fire_risk_assessment", HasDeleteDataPermission, 'delete'
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

        queryset = RequirementDefect.objects.filter(filter_mapping.get(data_access_value, Q()), pk=self.kwargs.get('pk'))
        
        requirement_defect = queryset.first()
        
        if requirement_defect:
            # Proceed with the deletion
            requirement_defect.delete()
            messages.success(request, "requirement defect has been deleted successfully!")
            return create_api_response(status_code=status.HTTP_404_NOT_FOUND,
                                        message="Your requirement defect has been deleted successfully!", )
        else:
            messages.error(request, "requirement defect not found OR You are not authorized to perform this action.")
            return create_api_response(status_code=status.HTTP_404_NOT_FOUND,
                                        message="requirement defect not found OR You are not authorized to perform this action.", )

class RequirementRemoveDocumentView(generics.DestroyAPIView):
    """
    View to remove a document associated with a requirement.
    """
    swagger_schema = None
    
    def destroy(self, request, *args, **kwargs):
        """
        Handles DELETE request to remove the document associated with a requirement.
        """
        requirement_id = kwargs.get('requirement_id')
        if requirement_id:
            requirement_instance = RequirementAsset.objects.filter(requirement_id=requirement_id, pk=  kwargs.get('document_id')).get()
            if requirement_instance and requirement_instance.document_path: 
                
                s3_client.delete_object(Bucket=settings.AWS_BUCKET_NAME, Key = requirement_instance.document_path)
                requirement_instance.delete()
            return Response(
                {"message": "Your requirement has been deleted successfully."},
                status=status.HTTP_204_NO_CONTENT
            )
        else:
            return Response(
                {"message": "Requirement not found OR you don't have permission to delete."},
                status=status.HTTP_404_NOT_FOUND
            )

class RequirementDefectRemoveDocumentView(generics.DestroyAPIView):
    """
    View to remove a document associated with a requirement defect.
    """
    swagger_schema = None
    
    def destroy(self, request, *args, **kwargs):
        """
        Handles DELETE request to remove the document associated with a requirement defect.
        """
        defect_id = kwargs.get('defect_id')
        if defect_id:
            defect_instance = RequirementDefectDocument.objects.filter(defect_id=defect_id, pk=kwargs.get('pk') ).get()
            if defect_instance and defect_instance.document_path: 
                
                s3_client.delete_object(Bucket=settings.AWS_BUCKET_NAME, Key = defect_instance.document_path)
                defect_instance.delete()
            return Response(
                {"message": "Your requirement defect has been deleted successfully."},
                status=status.HTTP_204_NO_CONTENT
            )
        else:
            return Response(
                {"message": "Requirement Defect not found OR you don't have permission to delete."},
                status=status.HTTP_404_NOT_FOUND
            )


class RequirementQSAddView(CustomAuthenticationMixin, generics.CreateAPIView):
    
    def post(self, request, *args, **kwargs):
        customer_id = kwargs.get('customer_id', None)
            
        try:
            customer_data = get_customer_data(customer_id)
            if customer_data:
                requirement_ids = request.data.get('selectedReqIds')
                quantity_sureveyor_id = request.data.get('qsSelect')
                
                
                requirments = Requirement.objects.filter(pk__in=ast.literal_eval(requirement_ids))
                quantity_sureveyor = User.objects.filter(pk=quantity_sureveyor_id).first()

                for requirement in requirments:
                    requirement.quantity_surveyor = quantity_sureveyor
                    requirement.status = "to-surveyor"
                    requirement.save()
                
                messages.success(request, "Updated Quantity Surveyour successfully")        
                return redirect(reverse('customer_requirement_list', kwargs={'customer_id': customer_id}))    
            else:
                messages.error(request, "You are not authorized to perform this action")
                return redirect(reverse('customer_requirement_list', kwargs={'customer_id': customer_id}))    
        
        except Exception as e:
            print(e)
            messages.error(request, "Something went wrong !")
            return redirect(reverse('customer_requirement_list', kwargs={'customer_id': customer_id}))    

class RequirementSurveyorAddView(CustomAuthenticationMixin, generics.CreateAPIView):
    
    def post(self, request, *args, **kwargs):
        customer_id = kwargs.get('customer_id', None)
            
        try:
            customer_data = get_customer_data(customer_id)
            if customer_data:
                requirement_ids = request.data.get('selectedIds')
                sureveyor_id = request.data.get('sureveyorselect')
                
                requirments = Requirement.objects.filter(pk__in=ast.literal_eval(requirement_ids))
                sureveyor = User.objects.filter(pk=sureveyor_id).first()
                
                for requirement in requirments:
                    requirement.surveyor = sureveyor
                    requirement.status = "assigned-to-surveyor"
                    requirement.save()
                
                messages.success(request, "Updated sureveyor successfully")        
                return redirect(reverse('customer_requirement_list', kwargs={'customer_id': customer_id}))    
            else:
                messages.error(request, "You are not authorized to perform this action")
                return redirect(reverse('customer_requirement_list', kwargs={'customer_id': customer_id}))    
        
        except Exception as e:
            print(e)
            messages.error(request, "Something went wrong !")
            return redirect(reverse('customer_requirement_list', kwargs={'customer_id': customer_id}))    

                
        