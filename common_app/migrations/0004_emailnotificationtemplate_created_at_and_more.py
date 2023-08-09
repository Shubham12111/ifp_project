# Generated by Django 4.2.3 on 2023-08-08 17:26

import ckeditor.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('common_app', '0003_emailnotificationtemplate'),
    ]

    operations = [
        migrations.AddField(
            model_name='emailnotificationtemplate',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name='emailnotificationtemplate',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, null=True),
        ),
        migrations.AlterField(
            model_name='emailnotificationtemplate',
            name='content',
            field=ckeditor.fields.RichTextField(blank=True, null=True),
        ),
    ]
