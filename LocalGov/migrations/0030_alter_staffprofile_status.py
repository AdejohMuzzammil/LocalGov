# Generated by Django 5.1.2 on 2024-11-21 08:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('LocalGov', '0029_alter_staffprofile_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='staffprofile',
            name='status',
            field=models.CharField(choices=[('pending', 'Pending'), ('approved', 'Approved'), ('declined', 'Declined'), ('removed', 'Removed')], default='pending', max_length=10),
        ),
    ]
