# Generated by Django 5.1.2 on 2024-12-04 12:29

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('LocalGov', '0054_alter_replytoreply_options'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='comment',
            options={'ordering': ['-date_commented']},
        ),
        migrations.AlterModelOptions(
            name='reply',
            options={'ordering': ['-date_commented'], 'verbose_name': 'Reply', 'verbose_name_plural': 'Replies'},
        ),
        migrations.AlterModelOptions(
            name='replytoreply',
            options={'ordering': ['-date_commented'], 'verbose_name_plural': 'Replies to Reply'},
        ),
    ]
