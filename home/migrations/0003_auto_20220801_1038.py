# Generated by Django 2.2.28 on 2022-08-01 10:38

import ckeditor.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0002_feedback'),
    ]

    operations = [
        migrations.AlterField(
            model_name='feedback',
            name='body',
            field=ckeditor.fields.RichTextField(),
        ),
    ]