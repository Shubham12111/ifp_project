from django.db import models
from authentication.models import User
from ckeditor.fields import RichTextField

# Choices for the 'status' field
STATUS_CHOICES = (
    ('pending', 'Pending'),
    ('in-progress', 'In Progress'),
    ('completed', 'Completed')
)

# Choices for the 'priority' field
PRIORITY_CHOICES = (
    ('high', 'High'),
    ('medium', 'Medium'),
    ('low', 'Low')
)

class Module(models.Model):
    """
    Represents a module in your application.
    """
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Todo(models.Model):
    """
    Represents a to-do item in your application.
    """
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name="userid")
    module = models.ForeignKey(Module, on_delete=models.CASCADE, null=True)
    title = models.CharField(max_length=200)
    description = RichTextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', help_text='The status of the to-do item.')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='Low', help_text='The priority of the to-do item.')
    start_date = models.DateField()
    end_date = models.DateField()
    completed_at = models.DateField(null=True, blank=True, help_text='The date when the to-do item was completed.')
    assigned_to = models.ForeignKey(User, on_delete=models.CASCADE, related_name="assignedto", verbose_name="Assigned To")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
    

class Comment(models.Model):
    """
    Represents a comment on a to-do item.
    """
    todo_id = models.ForeignKey(Todo, on_delete=models.CASCADE)
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = RichTextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', help_text='The status of the comment.')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Comment #{self.id} for {self.todo_id.title}"
