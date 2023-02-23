# Generated by Django 2.2.28 on 2022-11-23 11:09

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0022_auto_20221123_0834'),
    ]

    operations = [
        migrations.CreateModel(
            name='Industry',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=255, null=True)),
                ('create_at', models.DateField(auto_now=True)),
            ],
        ),
        migrations.RemoveField(
            model_name='industryexperience',
            name='type',
        ),
        migrations.AddField(
            model_name='industryexperience',
            name='industry',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='industry_name', to='users.Industry'),
        ),
    ]
