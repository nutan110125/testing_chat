# Generated by Django 3.0.8 on 2020-07-22 14:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0024_auto_20200722_1958'),
    ]

    operations = [
        migrations.AlterField(
            model_name='myusers',
            name='device_id',
            field=models.TextField(verbose_name='Device id'),
        ),
    ]
