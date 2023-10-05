from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics, permissions, filters,status
from requirement_management.models import Requirement
from rest_framework.renderers import TemplateHTMLRenderer, JSONRenderer
from requirement_management.models import Quotation
from .serializers import QuotationSerializer
from django.shortcuts import render
from django.views.generic.base import View
from drf_yasg.utils import swagger_auto_schema

from infinity_fire_solutions.response_schemas import create_api_response, convert_serializer_errors, render_html_response

class ApprovedQuotationListView(generics.ListAPIView):
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    serializer_class = QuotationSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['customer_id__first_name', 'customer_id__last_name']
    template_name = 'approved_quotation_list.html'

    def get_queryset(self):
        customer_id = self.request.query_params.get('customer_id')
        queryset = Quotation.objects.filter(status="approved")
        if customer_id:
            queryset = queryset.filter(customer_id=customer_id)
        return queryset
    def get(self, request, *args, **kwargs):
        customer_id = self.request.query_params.get('customer_id')
        queryset = self.get_queryset()
        customer_data = {}
        if request.accepted_renderer.format == 'html':
            context = {
                'approved_quotation': queryset,
                'customer_id': customer_id,
                'customer_data': customer_data
                }
            return render(request, self.template_name, context)
        else:
            messages.error(request, "You are not authorized to perform this action")
            return Response(status=status.HTTP_403_FORBIDDEN)



