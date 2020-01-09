from django.contrib import admin
from .models import ScrapeTarget, ScrapeResult

# Register your models here.
admin.site.register(ScrapeTarget)
admin.site.register(ScrapeResult)
