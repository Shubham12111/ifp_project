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



class RequirementReportsListView(CustomAuthenticationMixin,generics.ListAPIView):
    
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
                    'report_list':report_list
                    }
               

                return render_html_response(context, self.template_name)
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