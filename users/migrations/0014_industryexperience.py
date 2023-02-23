# Generated by Django 2.2.28 on 2022-10-14 10:34

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0013_auto_20221005_1416'),
    ]

    operations = [
        migrations.CreateModel(
            name='IndustryExperience',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(max_length=100)),
                ('profile', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='industry', to='users.Profile')),
            ],
        ),
    ]