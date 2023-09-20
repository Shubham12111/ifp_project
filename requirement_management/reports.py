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
from .views import filter_requirements,requirement_image
import ast
import os
import pdfkit
from django.template.loader import render_to_string
from infinity_fire_solutions.email import *


class RequirementReportsListView(CustomAuthenticationMixin,generics.ListAPIView):
    """
    View to list requirement reports.

    This view lists the requirement reports based on the authenticated user's permissions and the specified
    customer's ID. It allows searching by customer first name or last name and provides sorting options.

    Attributes:
        serializer_class (serializers.Serializer): The serializer class for the view.
        renderer_classes (list): The renderer classes used for rendering the view's response.
        filter_backends (list): The filter backends used for filtering the queryset.
        search_fields (list): The fields used for searching.
        template_name (str): The name of the HTML template used for rendering the response.
        ordering_fields (list): The fields used for ordering the queryset.

    Methods:
        get_queryset: Get the filtered queryset for requirements based on the authenticated user.
        get: Handle GET requests for listing requirement reports and rendering HTML responses.
    """

    serializer_class = CustomerSerializer
    renderer_classes = [TemplateHTMLRenderer,JSONRenderer]
    filter_backends = [filters.SearchFilter]
    search_fields = ['customer_id__first_name', 'customer_id__last_name']
    template_name = 'report.html'
    ordering_fields = ['created_at'] 

    def get_queryset(self):
        """
        Get the filtered queryset for requirements based on the authenticated user.
        """
        authenticated_user, data_access_value = check_authentication_and_permissions(
           self,"fire_risk_assessment", HasCreateDataPermission, 'detail'
        )
        
        queryset = filter_requirements(data_access_value, self.request.user, self.kwargs.get('customer_id'))
        queryset = queryset.filter(pk=self.kwargs.get('requirement_id')).first()
        
        return queryset


    @swagger_auto_schema(auto_schema=None)
    def get(self, request, *args, **kwargs):
        customer_data = User.objects.filter(id=kwargs.get('customer_id')).first()
        if customer_data:
            # This method handles GET requests for updating an existing Requirement object.
            if request.accepted_renderer.format == 'html':
                instance = self.get_queryset()
                
                if instance:
                    document_paths = []
                    document_paths = requirement_image(instance)
                    
                    report_list = Report.objects.filter(requirement_id=instance)
                    for report in report_list:

                        if report.pdf_path:
                            pdf_url =  generate_presigned_url(report.pdf_path)
                            report.pdf_url = pdf_url
                        else:
                            report.pdf_url = None


                    context = {
                        'requirement_instance': instance,  
                        'document_paths': document_paths,
                        'customer_id': kwargs.get('customer_id'),
                        'report_list':report_list,
                        'customer_data':customer_data
                        }
                

                    return render_html_response(context, self.template_name)
                else:
                    messages.error(request, "You are not authorized to perform this action")
                    return redirect(reverse('customer_requirement_list', kwargs={'customer_id': kwargs.get('customer_id')}))
        else:
            messages.error(request, "You are not authorized to perform this action")
            return redirect(reverse('customer_requirement_list', kwargs={'customer_id': kwargs.get('customer_id')}))


class ReportRemoveView(generics.DestroyAPIView):
    """
    View to remove a document associated with a requirement defect.
    """
    swagger_schema = None
    
    def destroy(self, request, *args, **kwargs):
        """
        Handles DELETE request to remove the document associated with a requirement defect.
        """
        report_id = kwargs.get('pk')
        if report_id:
            instance = Report.objects.filter(pk=report_id)
            instance.delete()
            return Response(
                {"message": "Your report has been deleted successfully."},
                status=status.HTTP_204_NO_CONTENT
            )
        else:
            return Response(
                {"message": "Requirement Report not found OR you don't have permission to delete."},
                status=status.HTTP_404_NOT_FOUND
            )

class ReportView(CustomAuthenticationMixin,generics.ListAPIView):
    """
    View to display a requirement report.

    This view displays a requirement report based on the authenticated user's permissions, the specified
    customer's ID, and the report ID. It allows searching by customer first name or last name and provides
    sorting options.

    Attributes:
        serializer_class (serializers.Serializer): The serializer class for the view.
        renderer_classes (list): The renderer classes used for rendering the view's response.
        filter_backends (list): The filter backends used for filtering the queryset.
        search_fields (list): The fields used for searching.
        template_name (str): The name of the HTML template used for rendering the response.
        ordering_fields (list): The fields used for ordering the queryset.

    Methods:
        get_queryset: Get the filtered queryset for requirements based on the authenticated user.
        get: Handle GET requests for displaying a requirement report and rendering HTML responses.
    """
    
    serializer_class = CustomerSerializer
    renderer_classes = [TemplateHTMLRenderer,JSONRenderer]
    filter_backends = [filters.SearchFilter]
    search_fields = ['customer_id__first_name', 'customer_id__last_name']
    template_name = 'report_view.html'
    ordering_fields = ['created_at'] 

    def get_queryset(self):
        """
        Get the filtered queryset for requirements based on the authenticated user.
        """
        authenticated_user, data_access_value = check_authentication_and_permissions(
           self,"fire_risk_assessment", HasCreateDataPermission, 'detail'
        )
        
        queryset = filter_requirements(data_access_value, self.request.user, self.kwargs.get('customer_id'))
        queryset = queryset.filter(pk=self.kwargs.get('requirement_id')).first()
        
        return queryset


    @swagger_auto_schema(auto_schema=None)
    def get(self, request, *args, **kwargs):
        customer_data = User.objects.filter(id=kwargs.get('customer_id')).first()
        if customer_data:
            report_id = kwargs.get('pk')
            # This method handles GET requests for updating an existing Requirement object.
            if request.accepted_renderer.format == 'html':
                requirement_instance = self.get_queryset()
                
                report_instance = Report.objects.filter(pk=report_id).first()
                
                if report_instance:
                    document_paths = []
                    document_paths = requirement_image(requirement_instance)
                    if report_instance.pdf_path:
                        pdf_url =  generate_presigned_url(report_instance.pdf_path)
                        report_instance.pdf_url = pdf_url
                    else:
                        report_instance.pdf_url = None

                    if report_instance.signature_path:
                        signature_path =  generate_presigned_url(report_instance.signature_path)
                        report_instance.signature_path = signature_path
                    else:
                        report_instance.pdf_url = None


                    context = {
                        'requirement_instance': requirement_instance,  
                        'report_instance':report_instance,
                        'document_paths': document_paths,
                        'customer_id': kwargs.get('customer_id'),
                        'customer_data':customer_data
                        }
                

                    return render_html_response(context, self.template_name)
                else:
                    messages.error(request, "You are not authorized to perform this action")
                    return redirect(reverse('customer_requirement_list', kwargs={'customer_id': kwargs.get('customer_id')}))
        else:
            messages.error(request, "You are not authorized to perform this action")
            return redirect(reverse('customer_requirement_list', kwargs={'customer_id': kwargs.get('customer_id')}))


class ReportEdit(CustomAuthenticationMixin,generics.ListAPIView):
    """
    View to edit a requirement report.

    This view allows users to edit a requirement report. It provides functionality for updating comments
    and status of the report, generating a PDF version of the report, and sending an email notification
    to the quantity surveyor upon report submission.

    Attributes:
        serializer_class (serializers.Serializer): The serializer class for the view.
        renderer_classes (list): The renderer classes used for rendering the view's response.
        filter_backends (list): The filter backends used for filtering the queryset.
        search_fields (list): The fields used for searching.
        template_name (str): The name of the HTML template used for rendering the response.
        ordering_fields (list): The fields used for ordering the queryset.
        pdf_options (dict): Options for generating the PDF from HTML content.

    Methods:
        save_pdf_from_html: Save a PDF file from HTML content.
        get_queryset: Get the filtered queryset for requirements based on the authenticated user.
        get: Handle GET requests for editing a requirement report and rendering HTML responses.
        post: Handle POST requests for updating a requirement report, generating a PDF, and sending emails.
    """

    
    serializer_class = CustomerSerializer
    renderer_classes = [TemplateHTMLRenderer,JSONRenderer]
    filter_backends = [filters.SearchFilter]
    search_fields = ['customer_id__first_name', 'customer_id__last_name']
    template_name = 'report_edit.html'
    ordering_fields = ['created_at'] 
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
        Get the filtered queryset for requirements based on the authenticated user.
        """
        authenticated_user, data_access_value = check_authentication_and_permissions(
           self,"fire_risk_assessment", HasCreateDataPermission, 'detail'
        )
        
        queryset = filter_requirements(data_access_value, self.request.user, self.kwargs.get('customer_id'))
        queryset = queryset.filter(pk=self.kwargs.get('requirement_id')).first()
        
        return queryset


    @swagger_auto_schema(auto_schema=None)
    def get(self, request, *args, **kwargs):
        customer_data = User.objects.filter(id=kwargs.get('customer_id')).first()
        if customer_data:
            report_id = kwargs.get('pk')
            # This method handles GET requests for updating an existing Requirement object.
            if request.accepted_renderer.format == 'html':
                requirement_instance = self.get_queryset()
                
                report_instance = Report.objects.filter(pk=report_id).first()
                
                if report_instance:
                    document_paths = []
                    document_paths = requirement_image(requirement_instance)
                    if report_instance.pdf_path:
                        pdf_url =  generate_presigned_url(report_instance.pdf_path)
                        report_instance.pdf_url = pdf_url
                    else:
                        report_instance.pdf_url = None

                    if report_instance.signature_path:
                        signature_path =  generate_presigned_url(report_instance.signature_path)
                        report_instance.signature_path = signature_path
                    else:
                        report_instance.pdf_url = None


                    context = {
                        'requirement_instance': requirement_instance,  
                        'report_instance':report_instance,
                        'document_paths': document_paths,
                        'customer_id': kwargs.get('customer_id'),
                        'customer_data':customer_data
                        }
                

                    return render_html_response(context, self.template_name)
                else:
                    messages.error(request, "You are not authorized to perform this action")
                    return redirect(reverse('customer_requirement_list', kwargs={'customer_id': kwargs.get('customer_id')}))
        else:
            messages.error(request, "You are not authorized to perform this action")
            return redirect(reverse('customer_requirement_list', kwargs={'customer_id': kwargs.get('customer_id')}))
    
    @swagger_auto_schema(auto_schema=None)
    def post(self, request, *args, **kwargs):
        report_id = kwargs.get('pk')
        report_instance = Report.objects.filter(pk=report_id).first()
        report_instance.comments = request.POST.get('comments')
        report_instance.status =  request.POST.get('status')
        report_instance.save()

        if report_instance:
            if report_instance.status == "submit":
                all_report_defects = report_instance.defect_id.all()
                
                requirement_document_images = RequirementAsset.objects.filter(requirement_id=report_instance.requirement_id.id)
                requirement_document_images_serializer = RequirementAssetSerializer(requirement_document_images, many=True)

                requirement_defect_images = RequirementDefectDocument.objects.filter(defect_id__in=all_report_defects)
                requirement_defect_images_serializer = RequirementDefectDocumentSerializer(requirement_defect_images, many=True)

                
                if report_instance.signature_path:
                    signature_data_url = generate_presigned_url(report_instance.signature_path)
                else:
                    signature_data_url = ""
                    
                context = {
                    'requirement_instance': report_instance.requirement_id,
                    'requirement_defects': all_report_defects,
                    'requirement_images': requirement_document_images_serializer.data,
                    'requirement_defect_images': requirement_defect_images_serializer.data,
                    'comment': report_instance.comments,
                    'signature_data_url':signature_data_url,
                }
                    
                unique_pdf_filename = f"{str(uuid.uuid4())}_report_{report_instance.id}.pdf"
                
                pdf_file = self.save_pdf_from_html(context=context, file_name=unique_pdf_filename)
                pdf_path = f'requirement/{report_instance.requirement_id.id}/report/pdf'
                
                
                
                upload_signature_to_s3(unique_pdf_filename, pdf_file, pdf_path)
                
                report_instance.pdf_path = f'requirement/{report_instance.requirement_id.id}/report/pdf/{unique_pdf_filename}'
                report_instance.save()
                
                # send email to QS
                if report_instance.requirement_id.quantity_surveyor and instance.surveyor:
                    context = {'user': report_instance.requirement_id.quantity_surveyor,'surveyor': report_instance.requirement_id.surveyor,'site_url': get_site_url(request) }

                    email = Email()
                    email.send_mail(report_instance.requirement_id.quantity_surveyor.email, 'email_templates/report.html', context, "Submission of Survey Report")

                messages.success(request, "Congratulations! your requirement report has been added successfully. ")
                return create_api_response(status_code=status.HTTP_404_NOT_FOUND,
                                            message="Congratulations! your requirement report has been added successfully.", )
        
        else:
            messages.error(request, "You are not authorized to perform this action")
            return redirect(reverse('customer_requirement_list', kwargs={'customer_id': kwargs.get('customer_id')}))
    