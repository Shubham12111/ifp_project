# Generated by Django 4.2.3 on 2023-11-21 08:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('requirement_management', '0035_requirement_due_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='requirement',
            name='due_date',
            field=models.DateField(blank=True, null=True),
        ),
    ]
