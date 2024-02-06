# Generated by Django 4.2.3 on 2024-02-02 13:10

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('work_planning_management', '0036_job_end_date_job_start_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='job',
            name='customer_id',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]
