# Generated by Django 3.2.10 on 2022-07-05 22:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('radio', '0008_system_rr_system_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='globalannouncement',
            name='name',
            field=models.CharField(max_length=80),
        ),
    ]
