# Generated by Django 4.2.3 on 2023-07-31 07:10

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0006_user_roles_alter_userrolepermission_module'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='roles',
        ),
        migrations.AlterField(
            model_name='userrolepermission',
            name='module',
            field=models.CharField(choices=[('contact', 'Contact'), ('costumer', 'Costumer'), ('todo', 'ToDo')], max_length=100),
        ),
        migrations.AddField(
            model_name='user',
            name='roles',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='authentication.userrole', verbose_name='UserRole'),
        ),
    ]
