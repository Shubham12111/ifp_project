# Generated by Django 4.2.3 on 2023-08-18 17:24

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('purchase_order_management', '0002_purchaseorderinvoice_purchaseorderreceivedinventory'),
    ]

    operations = [
        migrations.RenameField(
            model_name='purchaseorderinvoice',
            old_name='invoice_id',
            new_name='invoice_number',
        ),
    ]
