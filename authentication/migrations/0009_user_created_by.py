# Generated by Django 4.2.3 on 2023-08-02 06:39

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0008_user_company_name_user_customer_type_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='created_users', to=settings.AUTH_USER_MODEL),
        ),
    ]
