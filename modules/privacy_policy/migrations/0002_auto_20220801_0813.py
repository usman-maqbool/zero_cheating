# Generated by Django 2.2.28 on 2022-08-01 08:13

import ckeditor.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('privacy_policy', '0001_privacy_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='privacypolicy',
            name='body',
            field=ckeditor.fields.RichTextField(),
        ),
    ]
