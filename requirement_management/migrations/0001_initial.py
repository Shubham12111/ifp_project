# Generated by Django 4.2.3 on 2023-08-04 16:52

import ckeditor.fields
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Requirement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description', ckeditor.fields.RichTextField()),
                ('UPRN', models.CharField(max_length=12, unique=True)),
                ('requirement_date_time', models.DateTimeField()),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('in-progress', 'In Progress'), ('executed', 'Executed')], default='pending', max_length=30)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('customer_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='customer_requirement', to=settings.AUTH_USER_MODEL)),
                ('quality_surveyor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='surveyor_requirement', to=settings.AUTH_USER_MODEL)),
                ('user_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_requirement', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='RequirementDefect',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.TextField(max_length=256)),
                ('description', ckeditor.fields.RichTextField()),
                ('defect_period', models.DateTimeField()),
                ('due_date', models.DateTimeField()),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('in-progress', 'In Progress'), ('executed', 'Executed')], default='pending', max_length=30)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('requirement_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='requirement_management.requirement')),
            ],
        ),
        migrations.CreateModel(
            name='RequirementDocument',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('document_path', models.CharField(max_length=256)),
                ('create_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('defect_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='requirement_management.requirementdefect')),
                ('requirement_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='requirement_management.requirement')),
            ],
        ),
    ]
