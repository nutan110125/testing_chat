# Generated by Django 2.2.4 on 2020-07-24 06:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0028_sharevideo'),
    ]

    operations = [
        migrations.AddField(
            model_name='sharevideo',
            name='share_count',
            field=models.BigIntegerField(default=0, verbose_name='Total share count'),
        ),
    ]
