# Generated by Django 5.1.2 on 2024-11-27 15:14

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('LocalGov', '0050_alter_reply_options'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='staffpostnestedreply',
            options={'verbose_name': 'Staff Nested Reply', 'verbose_name_plural': 'Staff Nested Replies'},
        ),
        migrations.AlterModelOptions(
            name='staffpostreply',
            options={'verbose_name': 'Staff Post Reply', 'verbose_name_plural': 'Staff Post Replies'},
        ),
        migrations.CreateModel(
            name='ReplyToReply',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.TextField()),
                ('date_commented', models.DateTimeField(auto_now_add=True)),
                ('dislike_count', models.ManyToManyField(blank=True, related_name='disliked_reply_to_replies', to=settings.AUTH_USER_MODEL)),
                ('like_count', models.ManyToManyField(blank=True, related_name='liked_reply_to_replies', to=settings.AUTH_USER_MODEL)),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='child_replies', to='LocalGov.replytoreply')),
                ('reply', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='nested_replies', to='LocalGov.reply')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Reply to Reply',
                'verbose_name_plural': 'Replies to Replies',
            },
        ),
    ]
