# Generated by Django 4.2.3 on 2023-12-08 11:39

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0020_alter_userrolepermission_module'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='user',
            options={'ordering': ['-id']},
        ),
    ]
