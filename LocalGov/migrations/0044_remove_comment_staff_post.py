# Generated by Django 5.1.2 on 2024-11-25 15:29

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('LocalGov', '0043_comment_reply'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='comment',
            name='staff_post',
        ),
    ]
