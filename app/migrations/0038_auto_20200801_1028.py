# Generated by Django 2.2.4 on 2020-08-01 04:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0037_auto_20200726_1559'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='carddetail',
            options={'ordering': ('-created_at',), 'verbose_name_plural': 'User Card Detail'},
        ),
        migrations.AlterModelOptions(
            name='chats',
            options={'ordering': ('-created_at',), 'verbose_name_plural': 'User Chats'},
        ),
        migrations.AddField(
            model_name='videoaudio',
            name='title',
            field=models.TextField(blank=True, null=True, verbose_name='Audio Title'),
        ),
    ]
