# Generated by Django 2.2.28 on 2022-08-04 08:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_auto_20220714_1509'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='primary_expertise',
            field=models.ManyToManyField(blank=True, null=True, related_name='primary', to='users.UserExpertise'),
        ),
        migrations.AlterField(
            model_name='profile',
            name='secondary_expertise',
            field=models.ManyToManyField(blank=True, null=True, related_name='secondary', to='users.UserExpertise'),
        ),
    ]
