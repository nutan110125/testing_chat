# Generated by Django 2.2.4 on 2020-07-26 06:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0034_auto_20200726_1213'),
    ]

    operations = [
        migrations.AlterField(
            model_name='paymentdetail',
            name='order_currency',
            field=models.CharField(blank=True, max_length=20, null=True, verbose_name='order currency'),
        ),
    ]
