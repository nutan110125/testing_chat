# Generated by Django 3.0.8 on 2020-07-22 09:04

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0021_myusers_is_online'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='AdminChats',
            new_name='Chats',
        ),
    ]
