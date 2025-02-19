# Generated by Django 4.2.3 on 2023-08-07 10:12

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('cities_light', '0011_alter_city_country_alter_city_region_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Vendor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_name', models.CharField(max_length=255)),
                ('last_name', models.CharField(max_length=255)),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('phone_number', models.CharField(max_length=20)),
                ('company', models.CharField(blank=True, max_length=255, null=True)),
                ('vat_number', models.CharField(blank=True, max_length=20, null=True)),
                ('pan_number', models.CharField(blank=True, max_length=20, null=True)),
                ('tax_preference', models.CharField(blank=True, choices=[('taxable', 'Taxable'), ('tax_exempt', 'Tax Exempt')], max_length=30, null=True)),
                ('address', models.CharField(blank=True, max_length=255, null=True)),
                ('post_code', models.CharField(blank=True, max_length=10, null=True)),
                ('vendor_status', models.CharField(blank=True, choices=[('pending', 'Pending'), ('in-progress', 'In Progress'), ('completed', 'Completed')], max_length=30, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('country', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='cities_light.country')),
                ('county', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='cities_light.region', verbose_name='County')),
                ('town', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='cities_light.city')),
                ('user_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='vendor_user', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
