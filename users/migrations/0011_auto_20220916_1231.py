# Generated by Django 2.2.28 on 2022-09-16 12:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0010_profile_admin_note'),
    ]

    operations = [
        migrations.AddField(
            model_name='businessprofile',
            name='blrub',
            field=models.TextField(blank=True, max_length=800, null=True),
        ),
        migrations.AddField(
            model_name='businessprofile',
            name='poc',
            field=models.CharField(blank=True, max_length=250, null=True),
        ),
        migrations.AddField(
            model_name='businessprofile',
            name='website',
            field=models.URLField(blank=True, max_length=500, null=True),
        ),
    ]
