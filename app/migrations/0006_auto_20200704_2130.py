# Generated by Django 3.0.8 on 2020-07-05 04:30

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0005_auto_20200704_0255'),
    ]

    operations = [
        migrations.AlterField(
            model_name='myusers',
            name='gender',
            field=models.CharField(blank=True, max_length=20, null=True, verbose_name='Gender'),
        ),
        migrations.CreateModel(
            name='CommentsActions',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(blank=True, max_length=20, null=True, verbose_name='Actions of comment')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created Date')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated Date')),
                ('comment_id', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='main_comment_action', to='app.UserVideosCommentAction')),
                ('reply_id', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='reply_comment_action', to='app.UserCommentReply')),
            ],
            options={
                'verbose_name_plural': 'Videos Comment or Reply Action',
            },
        ),
    ]
