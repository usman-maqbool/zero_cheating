# Generated by Django 2.2.28 on 2022-11-23 11:41

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0023_auto_20221123_1109'),
    ]

    operations = [
        migrations.AlterField(
            model_name='industryexperience',
            name='profile',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='industry_profile', to='users.Profile'),
        ),
    ]
