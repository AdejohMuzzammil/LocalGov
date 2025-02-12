# Generated by Django 5.1.2 on 2024-11-26 10:55

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('LocalGov', '0045_staffpostcomment_staffpostreply'),
    ]

    operations = [
        migrations.AlterField(
            model_name='staffpostcomment',
            name='staff_post',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='staff_comments', to='LocalGov.staffpost'),
        ),
        migrations.AlterField(
            model_name='staffpostreply',
            name='comment',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='staff_replies', to='LocalGov.staffpostcomment'),
        ),
    ]
