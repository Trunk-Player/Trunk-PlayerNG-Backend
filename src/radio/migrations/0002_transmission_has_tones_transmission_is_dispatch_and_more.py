# Generated by Django 4.2.10 on 2024-02-10 00:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('radio', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='transmission',
            name='has_tones',
            field=models.BooleanField(db_index=True, default=False),
        ),
        migrations.AddField(
            model_name='transmission',
            name='is_dispatch',
            field=models.BooleanField(db_index=True, default=False),
        ),
        migrations.AddField(
            model_name='transmission',
            name='tones_detected',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='transmission',
            name='tones_meta',
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
