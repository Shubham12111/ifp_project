# Generated by Django 4.2.3 on 2023-07-24 05:49

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contact', '0008_alter_conversation_message'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='contact',
            options={'permissions': (('list_contact', 'Can list Contact'),)},
        ),
    ]
