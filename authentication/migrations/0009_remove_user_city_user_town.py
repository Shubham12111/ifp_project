# Generated by Django 4.2.3 on 2023-08-04 04:15

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('cities_light', '0011_alter_city_country_alter_city_region_and_more'),
        ('authentication', '0008_alter_userrolepermission_module'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='city',
        ),
        migrations.AddField(
            model_name='user',
            name='town',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='cities_light.city', verbose_name='Town'),
        ),
    ]
