# Generated by Django 4.2.3 on 2024-01-10 07:35

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('purchase_order_management', '0009_purchaseorder_location_type_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='purchaseorder',
            name='user_id',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]
