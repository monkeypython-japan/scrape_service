# Generated by Django 3.0 on 2019-12-24 07:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('registration', '0004_auto_20191220_0107'),
    ]

    operations = [
        migrations.AlterField(
            model_name='scrapetarget',
            name='interval',
            field=models.CharField(choices=[('h', 'HOUR'), ('d', 'DAY')], max_length=1, verbose_name='インターバル'),
        ),
    ]
