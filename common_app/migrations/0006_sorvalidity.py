# Generated by Django 4.2.3 on 2023-09-28 06:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('common_app', '0005_adminconfiguration'),
    ]

    operations = [
        migrations.CreateModel(
            name='SORValidity',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sor_expiration_date', models.DateTimeField(blank=True, help_text='The date and time when this item will expire.', null=True, verbose_name='Expiration Date')),
            ],
        ),
    ]
