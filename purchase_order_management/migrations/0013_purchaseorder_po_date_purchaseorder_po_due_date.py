# Generated by Django 4.2.3 on 2024-02-23 08:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('purchase_order_management', '0012_alter_purchaseorder_vendor_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='purchaseorder',
            name='po_date',
            field=models.DateField(null=True),
        ),
        migrations.AddField(
            model_name='purchaseorder',
            name='po_due_date',
            field=models.DateField(null=True),
        ),
    ]
