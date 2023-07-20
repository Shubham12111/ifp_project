from django.http import JsonResponse
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.renderers import TemplateHTMLRenderer,JSONRenderer
from infinity_fire_solutions.response_schemas import create_api_response
from .models import *

class ToDoListView(generics.ListAPIView):
    """ view to get the listing of all contacts
    """
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'todo_list.html'

    def get(self, request, *args, **kwargs):
        queryset = Todo.objects.filter(user_id=request.user)

        if request.accepted_renderer.format == 'html':
            # If the client accepts HTML, render the template
            return Response({'todo_list': queryset}, template_name=self.template_name)
        
        # # If the client accepts JSON (DataTable's request), handle server-side processing
        # draw = int(request.GET.get('draw', 1))
        # start = int(request.GET.get('start', 0))
        # length = int(request.GET.get('length', 10))
        # search_value = request.GET.get('search[value]', None)

        # if search_value:
        #     queryset = queryset.filter(title__icontains=search_value)

        # total_records = queryset.count()
        # queryset = queryset[start:start + length]

        # serializer = self.serializer_class(queryset, many=True)

        # print(queryset, queryset)
        # return JsonResponse({
        #     'draw': draw,
        #     'recordsTotal': total_records,
        #     'recordsFiltered': total_records,
        #     'data': serializer.data
        # })
    