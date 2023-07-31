# Generated by Django 4.2.3 on 2023-07-25 06:41

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='MenuItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('permission_required', models.BooleanField(default=False)),
                ('name', models.CharField(max_length=100)),
                ('url', models.CharField(max_length=200)),
                ('icon', models.CharField(max_length=100)),
                ('order', models.IntegerField()),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='children', to='common_app.menuitem')),
                ('permissions', models.ManyToManyField(blank=True, to='auth.group')),
            ],
        ),
    ]
