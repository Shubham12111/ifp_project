# Generated by Django 4.2.3 on 2023-10-19 09:14

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('work_planning_management', '0019_member_team'),
    ]

    operations = [
        migrations.CreateModel(
            name='STWJobAssignment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('start_time', models.TimeField()),
                ('end_time', models.TimeField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('assigned_to_member', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='work_planning_management.member')),
                ('assigned_to_team', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='work_planning_management.team')),
                ('stw_job', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='work_planning_management.stwjob')),
            ],
            options={
                'verbose_name': 'STW Job Assign',
                'verbose_name_plural': 'STW Job Assign',
            },
        ),
    ]
