# views.py
from django.shortcuts import render
from django.views import View
from .models import *

class MessageListView(View):
    template_name = 'messages.html'

    def get(self, request):
        messages = Contact.objects.all()
        return render(request, self.template_name, {'messages': messages})
