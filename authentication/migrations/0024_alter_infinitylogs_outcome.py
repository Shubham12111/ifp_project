# Generated by Django 4.2.3 on 2023-12-29 10:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0023_infinitylogs'),
    ]

    operations = [
        migrations.AlterField(
            model_name='infinitylogs',
            name='outcome',
            field=models.CharField(max_length=100),
        ),
    ]
