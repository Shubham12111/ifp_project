# Generated by Django 4.2.3 on 2023-09-06 07:55

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('requirement_management', '0014_alter_requirementdefect_action'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='RequirementDocument',
            new_name='RequirementDefectDocument',
        ),
        migrations.RemoveField(
            model_name='requirementdefectresponseimage',
            name='defect_response',
        ),
        migrations.RemoveField(
            model_name='requirement',
            name='requirement_date_time',
        ),
        migrations.AddField(
            model_name='requirement',
            name='action',
            field=models.TextField(default=None),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='requirementdefect',
            name='rectification_description',
            field=models.TextField(default=None),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='requirement',
            name='description',
            field=models.TextField(),
        ),
        migrations.AlterField(
            model_name='requirement',
            name='quantity_surveyor',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='surveyor_requirement', to=settings.AUTH_USER_MODEL),
        ),
        migrations.DeleteModel(
            name='RequirementDefectResponse',
        ),
        migrations.DeleteModel(
            name='RequirementDefectResponseImage',
        ),
    ]
