# Generated by Django 3.0.8 on 2020-07-22 15:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0026_auto_20200722_2025'),
    ]

    operations = [
        migrations.AlterField(
            model_name='usernewtoken',
            name='token',
            field=models.TextField(blank=True, null=True),
        ),
    ]
