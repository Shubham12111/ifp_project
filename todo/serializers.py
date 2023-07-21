# todo_app/serializers.py
from rest_framework import serializers
from .models import Todo

class TodoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Todo
        fields = ('id', 'user_id', 'module', 'title', 'description', 'status', 'priority', 'start_date', 'end_date', 'assigned_to', 'created_at', 'updated_at')


class TodoAddSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Todo
        fields = ('module', 'title', 'description', 'status', 'priority', 'start_date', 'end_date', 'assigned_to')
