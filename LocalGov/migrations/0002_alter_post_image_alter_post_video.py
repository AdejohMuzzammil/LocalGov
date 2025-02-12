# Generated by Django 5.1.2 on 2024-11-01 19:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('LocalGov', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='images/'),
        ),
        migrations.AlterField(
            model_name='post',
            name='video',
            field=models.FileField(blank=True, null=True, upload_to='videos/'),
        ),
    ]
