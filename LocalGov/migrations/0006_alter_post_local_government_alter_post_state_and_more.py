# Generated by Django 5.1.2 on 2024-11-11 08:22

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('LocalGov', '0005_post_location'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='local_government',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='post_local_governments', to='LocalGov.localgovernment'),
        ),
        migrations.AlterField(
            model_name='post',
            name='state',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='post_states', to='LocalGov.state'),
        ),
        migrations.CreateModel(
            name='ChairmanProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('profile_picture', models.ImageField(blank=True, null=True, upload_to='profile_pictures/')),
                ('bio', models.TextField(blank=True, null=True)),
                ('phone_number', models.CharField(blank=True, max_length=15, null=True)),
                ('email', models.EmailField(max_length=254)),
                ('local_government', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='chairman_profiles', to='LocalGov.localgovernment')),
                ('state', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='chairman_profiles', to='LocalGov.state')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
