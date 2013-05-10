from django.db import models

class Page(models.Model):
    url = models.CharField(max_length=200)
    onsale = models.BooleanField('on-sale')

    def __unicode__(self):
        return self.url
    
    class Meta:
        app_label = 'scraper'


