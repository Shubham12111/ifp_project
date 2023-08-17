# Generated by Django 4.2.3 on 2023-08-17 12:57

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('requirement_management', '0010_remove_requirement_document_path_requirementasset'),
    ]

    operations = [
        migrations.CreateModel(
            name='RequirementDefectResponse',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('rectification_description', models.TextField()),
                ('remedial_work', models.TextField()),
                ('status', models.CharField(choices=[('draft', 'Draft'), ('submitted', 'submitted')], max_length=20)),
                ('create_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('defect_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='requirement_management.requirementdefect')),
                ('surveyor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='RequirementDefectResponseImage',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('document_path', models.TextField()),
                ('create_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('defect_response', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='requirement_management.requirementdefectresponse')),
            ],
        ),
    ]
