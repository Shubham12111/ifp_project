# Generated by Django 4.2.3 on 2023-08-20 17:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0015_alter_userrole_description_alter_userrole_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userrolepermission',
            name='module',
            field=models.CharField(choices=[('contact', 'Contacts'), ('todo', 'ToDo'), ('customer', 'Customer'), ('fire_risk_assessment', 'Fire Risk Assessment'), ('surveyor', 'Surveyor'), ('stock_management', 'Stock Management'), ('invoicing', 'Invoicing')], max_length=100),
        ),
    ]
