# Generated by Django 4.2.3 on 2023-12-08 11:39

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('work_planning_management', '0031_alter_stwjobassignment_stw_job'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='events',
            options={'ordering': ['id'], 'verbose_name': 'Calendar Events', 'verbose_name_plural': 'Calendar Events'},
        ),
        migrations.AlterModelOptions(
            name='job',
            options={'ordering': ['id']},
        ),
        migrations.AlterModelOptions(
            name='jobdocument',
            options={'ordering': ['created_at'], 'verbose_name': 'Job Document', 'verbose_name_plural': 'Job Documents'},
        ),
        migrations.AlterModelOptions(
            name='member',
            options={'ordering': ['id'], 'verbose_name': 'Member', 'verbose_name_plural': 'Members'},
        ),
        migrations.AlterModelOptions(
            name='rlo',
            options={'ordering': ['id'], 'verbose_name': 'RLO', 'verbose_name_plural': 'RLO'},
        ),
        migrations.AlterModelOptions(
            name='sitepackasset',
            options={'ordering': ['id'], 'verbose_name': 'Sitepack Asset', 'verbose_name_plural': 'Sitepack Asset'},
        ),
        migrations.AlterModelOptions(
            name='sitepackdocument',
            options={'ordering': ['id']},
        ),
        migrations.AlterModelOptions(
            name='stwdefect',
            options={'ordering': ['id'], 'verbose_name': 'STW Defect', 'verbose_name_plural': 'STW Defect'},
        ),
        migrations.AlterModelOptions(
            name='stwjob',
            options={'ordering': ['id'], 'verbose_name': 'STW Job', 'verbose_name_plural': 'STW Job'},
        ),
        migrations.AlterModelOptions(
            name='stwjobassignment',
            options={'ordering': ['created_at'], 'verbose_name': 'STW Job Assign', 'verbose_name_plural': 'STW Job Assign'},
        ),
        migrations.AlterModelOptions(
            name='stwrequirements',
            options={'ordering': ['id'], 'verbose_name': 'STW Requirements', 'verbose_name_plural': 'STW Requirements'},
        ),
        migrations.AlterModelOptions(
            name='team',
            options={'ordering': ['id'], 'verbose_name': 'Team', 'verbose_name_plural': 'Teams'},
        ),
    ]
