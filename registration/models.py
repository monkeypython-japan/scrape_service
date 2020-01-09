from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class ScrapeTarget(models.Model):
    '''Scrape target with url & xpath'''
    class Meta:
        db_table = 'scrape_target'

    # Fields
    owner = models.ForeignKey(User, verbose_name='ユーザ', on_delete=models.CASCADE)
    name = models.CharField(verbose_name = 'フィールド名', max_length = 255)
    url =  models.URLField(verbose_name = 'URL')
    xpath = models.CharField(verbose_name = 'xpath',max_length=225)
    INTERVAL_OPTION = (
        ('h','HOUR'),
        ('d','DAY')
    )
    interval = models.CharField(verbose_name = 'インターバル',max_length=1, choices=INTERVAL_OPTION, blank=True, default='d')
    trigger_number = models.IntegerField(verbose_name = '開始時点',blank=True, default=0)
    description = models.TextField(verbose_name='概要', null=True, blank=True)

    # Desctiption
    def __str__(self):
        return self.name

class ScrapeResult(models.Model):
    '''Result of scrapeing'''
    class Meta:
        db_table = 'scrape_result'

    #Fields
    target = models.ForeignKey(ScrapeTarget, verbose_name = 'ScrapeTarget',on_delete = models.CASCADE)
    value = models.CharField(verbose_name = '採取値', max_length = 255)
    time = models.DateTimeField(verbose_name = '最終採取時間')

   # Desctiption
    def __str__(self):
        return self.value