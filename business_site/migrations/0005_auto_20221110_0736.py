# Generated by Django 2.2.28 on 2022-11-10 07:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('business_site', '0004_businesshourrequest_is_show'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='businesshourrequest',
            name='is_show',
        ),
        migrations.AddField(
            model_name='businesshourrequest',
            name='increase_hour',
            field=models.CharField(blank=True, choices=[('Weekly', 'Weekly'), ('One-Time', 'One-Time')], max_length=255, null=True),
        ),
    ]
