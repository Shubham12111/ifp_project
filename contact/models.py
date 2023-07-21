from django.db import models
from cities_light.models import City, Country, Region
from authentication.models import User


class ConversationType(models.Model):
    name = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class ContactType(models.Model):
    name = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Contact(models.Model):
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    first_name = models.CharField(max_length=30,null=True)
    last_name = models.CharField(max_length=30,null=True)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20)
    contact_type = models.ForeignKey(ContactType, on_delete=models.CASCADE)
    job_title = models.CharField(max_length=255, null=True, blank=True)
    company = models.CharField(max_length=255,null=True, blank=True)
    address = models.CharField(max_length=255 , null=True, blank=True)
    country = models.ForeignKey(Country, on_delete=models.CASCADE, null=True, blank=True)
    city = models.ForeignKey(City, on_delete=models.CASCADE, null=True, blank=True)
    state = models.ForeignKey(Region, on_delete=models.CASCADE, null=True, blank=True)
    pincode = models.CharField(max_length=10, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.first_name

class Conversation(models.Model):
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    contact_id = models.ForeignKey(Contact, on_delete=models.CASCADE)
    conversation_type = models.ForeignKey(ConversationType, on_delete=models.CASCADE)
    document_path = models.CharField(max_length=200, verbose_name="Document Path", null=True, blank=True)
    message = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

