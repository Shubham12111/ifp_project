# Generated by Django 4.2.3 on 2023-09-28 06:35

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('requirement_management', '0033_soritem_validity'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='soritem',
            name='validity',
        ),
    ]
