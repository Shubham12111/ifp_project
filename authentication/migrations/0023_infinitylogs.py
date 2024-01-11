# Generated by Django 4.2.3 on 2023-12-27 08:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0022_alter_user_country_alter_user_county_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='InfinityLogs',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('api', models.CharField(help_text='API URL', max_length=1024)),
                ('access_type', models.CharField(max_length=150)),
                ('ip_address', models.CharField(max_length=50)),
                ('page_slug', models.CharField(max_length=2000)),
                ('module', models.CharField(max_length=20)),
                ('action_type', models.CharField(max_length=10)),
                ('user_id', models.IntegerField()),
                ('username', models.CharField(max_length=100, null=True)),
                ('device_type', models.CharField(max_length=50)),
                ('browser', models.CharField(max_length=100)),
                ('outcome', models.CharField(max_length=20)),
                ('request_payload', models.TextField(null=True)),
                ('response_payload', models.TextField()),
                ('status_code', models.PositiveSmallIntegerField(db_index=True, help_text='Response status code')),
                ('elapsed_time', models.DecimalField(decimal_places=5, help_text='Server execution time (Not complete response time.)', max_digits=8)),
                ('affected_modules', models.TextField(null=True)),
                ('change_description', models.CharField(max_length=200, null=True)),
                ('previous_state', models.TextField(null=True)),
                ('new_state', models.TextField(null=True)),
                ('user_role', models.CharField(max_length=100, null=True)),
                ('body', models.TextField(null=True)),
                ('method', models.CharField(db_index=True, max_length=10)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'InfinityLogs',
                'verbose_name_plural': 'InfinityLogs ',
                'db_table': 'InfinityLogs',
            },
        ),
    ]
