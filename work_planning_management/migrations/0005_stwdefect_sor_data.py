# Generated by Django 4.2.3 on 2023-10-05 10:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('work_planning_management', '0004_stwdefect_stwdefectdocument_stwasset'),
    ]

    operations = [
        migrations.AddField(
            model_name='stwdefect',
            name='sor_data',
            field=models.JSONField(blank=True, null=True),
        ),
    ]
