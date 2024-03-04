# Generated by Django 4.2.3 on 2024-03-04 06:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0029_alter_userrole_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userrolepermission',
            name='module',
            field=models.CharField(choices=[('contact', 'Contacts'), ('task', 'Task'), ('customer', 'Customer'), ('estimation', 'Estimation'), ('fire_risk_assessment', 'Fire Risk Assessment'), ('survey', 'Survey (Scheduling)'), ('stock_management', 'Stock Management'), ('invoicing', 'Invoicing'), ('purchase_order', 'Purchase Order'), ('work_bank', 'Work Bank')], max_length=100),
        ),
    ]
