# Generated by Django 2.2.28 on 2022-11-19 06:44

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0019_auto_20221119_0631'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='userexpertise',
            name='type',
        ),
        migrations.AddField(
            model_name='userexpertise',
            name='expertise',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='expertise', to='users.Expertise'),
        ),
    ]
