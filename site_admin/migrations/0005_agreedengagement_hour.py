# Generated by Django 2.2.28 on 2022-11-04 17:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('site_admin', '0004_endingengagementrequest'),
    ]

    operations = [
        migrations.AddField(
            model_name='agreedengagement',
            name='hour',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
