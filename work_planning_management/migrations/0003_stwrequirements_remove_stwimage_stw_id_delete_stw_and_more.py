# Generated by Django 4.2.3 on 2023-10-04 09:04

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('customer_management', '0003_remove_billingaddress_pan_number'),
        ('work_planning_management', '0002_stwimage'),
    ]

    operations = [
        migrations.CreateModel(
            name='STWRequirements',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('UPRN', models.CharField(max_length=255, null=True)),
                ('RBNO', models.CharField(max_length=255, null=True)),
                ('description', models.TextField()),
                ('action', models.TextField()),
                ('status', models.CharField(choices=[('active', 'Active'), ('pending', 'Pending'), ('completed', 'Completed')], default='active', max_length=30)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('customer_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='stw_requirement', to=settings.AUTH_USER_MODEL)),
                ('site_address', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='customer_management.siteaddress')),
                ('user_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='stw_user', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'STW Requirements',
                'verbose_name_plural': 'STW Requirements',
            },
        ),
        migrations.RemoveField(
            model_name='stwimage',
            name='stw_id',
        ),
        migrations.DeleteModel(
            name='STW',
        ),
        migrations.DeleteModel(
            name='STWImage',
        ),
    ]
