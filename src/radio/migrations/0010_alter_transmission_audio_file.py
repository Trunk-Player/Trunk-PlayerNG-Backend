# Generated by Django 3.2.10 on 2022-09-09 22:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('radio', '0009_alter_globalannouncement_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='transmission',
            name='audio_file',
            field=models.FileField(max_length=250, upload_to='audio/%Y/%m/%d/'),
        ),
    ]