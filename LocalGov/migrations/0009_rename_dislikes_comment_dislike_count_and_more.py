# Generated by Django 5.1.2 on 2024-11-11 15:51

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('LocalGov', '0008_comment_dislikes_comment_likes_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='comment',
            old_name='dislikes',
            new_name='dislike_count',
        ),
        migrations.RenameField(
            model_name='comment',
            old_name='likes',
            new_name='like_count',
        ),
    ]
