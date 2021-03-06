# Generated by Django 3.0 on 2020-01-17 12:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('registration', '0008_auto_20191225_0550'),
    ]

    operations = [
        migrations.AddField(
            model_name='scrapetarget',
            name='last_execution_time',
            field=models.DateTimeField(blank=True, null=True, verbose_name='直近実行時間'),
        ),
        migrations.AlterField(
            model_name='scraperesult',
            name='time',
            field=models.DateTimeField(verbose_name='採取時間'),
        ),
        migrations.AlterField(
            model_name='scrapetarget',
            name='interval',
            field=models.CharField(blank=True, choices=[('H', 'HOUR'), ('D', 'DAY'), ('W', 'WEEK')], default='d', max_length=1, verbose_name='インターバル'),
        ),
    ]
