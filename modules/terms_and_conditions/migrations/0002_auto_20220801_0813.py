# Generated by Django 2.2.28 on 2022-08-01 08:13

import ckeditor.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('terms_and_conditions', '0001_terms_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='termandcondition',
            name='body',
            field=ckeditor.fields.RichTextField(),
        ),
    ]
