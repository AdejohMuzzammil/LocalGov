# Generated by Django 5.1.2 on 2024-11-21 11:11

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('LocalGov', '0030_alter_staffprofile_status'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='staffprofile',
            name='first_name',
        ),
        migrations.RemoveField(
            model_name='staffprofile',
            name='last_name',
        ),
    ]
