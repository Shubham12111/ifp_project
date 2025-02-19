# Generated by Django 4.2.3 on 2024-02-20 07:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('invoice_management', '0004_alter_invoice_submitted_at'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='invoice',
            options={'ordering': ['-updated_at'], 'verbose_name': 'Invoice', 'verbose_name_plural': 'Invoices'},
        ),
        migrations.AddField(
            model_name='invoice',
            name='billing_information_json',
            field=models.JSONField(default=dict, verbose_name='Billing Information Details'),
        ),
        migrations.AddField(
            model_name='invoice',
            name='paid_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Paid At'),
        ),
    ]
