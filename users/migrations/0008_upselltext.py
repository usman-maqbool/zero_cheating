# Generated by Django 2.2.28 on 2022-08-31 11:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0007_businessprofile_logo'),
    ]

    operations = [
        migrations.CreateModel(
            name='UpsellText',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('disclaimer_text', models.CharField(max_length=250)),
                ('active', models.BooleanField()),
            ],
        ),
    ]